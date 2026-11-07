"""Exercise the shipped app bundle with delayed network and timer responses."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]

HARNESS = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map(), timers = new Map(), stored = new Map();
let timerId = 0;
function element(id) {
  if (!elements.has(id)) elements.set(id, {
    value: '', textContent: '', innerHTML: '', disabled: false, inert: false,
    dataset: {}, style: {}, listeners: {},
    classList: {add(){}, remove(){}, toggle(){}},
    addEventListener(type, handler){this.listeners[type] = handler;},
    insertAdjacentHTML(){}, querySelectorAll(){return [];}
  });
  return elements.get(id);
}
const navigations = [], alerts = [];
const context = vm.createContext({
  URL, URLSearchParams, console, Promise, Number, String, Intl,
  document: {getElementById: element, querySelectorAll(){return [];},
    querySelector(selector){return selector === '.view.active' ? {id:'connect'} : null;}},
  location: {href:'https://vexmera.com/app?plan=pro', pathname:'/app', search:'', hash:'',
    assign(url){navigations.push(url);}, reload(){navigations.push('reload');}},
  history: {replaceState(){}}, navigator: {},
  sessionStorage: {getItem(key){return stored.get(key) || null;}, setItem(key,v){stored.set(key,v);}},
  setTimeout(fn){timers.set(++timerId,fn);return timerId;}, clearTimeout(id){timers.delete(id);},
  alert(message){alerts.push(message);},
  // Leave bootstrap pending; each case supplies its own offline API transport.
  fetch(){return new Promise(()=>{});}
});
context.window = context;
vm.runInContext(fs.readFileSync('static/app.js','utf8'),context);
const run = source => vm.runInContext(source,context);
const response = (data={}, ok=true) => ({ok,status:ok?200:503,json:async()=>data});
const tick = async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
"""


def _node(scenario: str) -> None:
    result = subprocess.run(
        ["node", "-e", HARNESS + "\n(async()=>{\n" + scenario + "\n})().catch(err=>{console.error(err);process.exit(1);});"],
        cwd=ROOT, text=True, capture_output=True, timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_debounced_profile_captures_company_and_workspace_at_edit_time():
    _node(r"""
    const writes = [];
    context.fetch = async(path,opts)=>{writes.push({path,body:JSON.parse(opts.body)});return response();};
    run("currentWorkspaceId=1; $('name').value='Company A'; saveProfile();");
    // Simulate a different form appearing before the debounce fires.
    run("currentWorkspaceId=2; $('name').value='Company B';");
    await run('flushProfile()');
    assert.equal(writes[0].path,'/api/company?workspace_id=1');
    assert.equal(writes[0].body.name,'Company A');
    """)


def test_profile_writes_are_serial_and_old_failure_does_not_restore_old_edit():
    _node(r"""
    const writes = [];let rejectFirst;
    context.fetch = (path,opts)=>{
      writes.push(JSON.parse(opts.body).name);
      if(writes.length===1)return new Promise((resolve,reject)=>{rejectFirst=reject;});
      return Promise.resolve(response());
    };
    run("currentWorkspaceId=1; $('name').value='First'; saveProfile();");
    const first=run('flushProfile()').catch(()=>{});await tick();
    run("$('name').value='Latest'; saveProfile();");
    const latest=run('flushProfile()');await tick();
    assert.deepEqual(writes,['First']);
    rejectFirst(new Error('offline'));await first;await latest;
    assert.deepEqual(writes,['First','Latest']);
    await run('flushProfile()');
    assert.deepEqual(writes,['First','Latest']);
    assert.match(element('profileState').textContent,/Sparad/);
    """)


def test_switch_waits_for_save_then_navigates_without_reusing_old_workspace_state():
    _node(r"""
    let completeSave;const writes=[];
    context.fetch=(path,opts)=>{writes.push(path);return new Promise(resolve=>{completeSave=resolve;});};
    run("currentWorkspaceId=1; $('name').value='Company A'; saveProfile(); $('workspaceSelect').value='2';");
    const switchDone=element('workspaceSelect').listeners.change();await tick();
    assert.equal(element('appShell').inert,true);
    assert.equal(navigations.length,0);
    assert.deepEqual(writes,['/api/company?workspace_id=1']);
    completeSave(response());await switchDone;
    assert.equal(navigations[0],'/app?workspace=2&view=connect');
    assert.equal(run('currentWorkspaceId'),1);
    assert.equal(run("initialWorkspace([{id:1},{id:2}],new URLSearchParams('workspace=2'))"),2);
    assert.equal(run("initialWorkspace([{id:1}],new URLSearchParams('workspace=999'))"),1);
    """)


def test_failed_save_blocks_switch_and_can_be_retried():
    _node(r"""
    context.fetch=async()=>response({detail:'offline'},false);
    run("currentWorkspaceId=1; $('name').value='Unsaved'; saveProfile(); $('workspaceSelect').value='2';");
    await element('workspaceSelect').listeners.change();
    assert.equal(navigations.length,0);
    assert.equal(element('workspaceSelect').value,'1');
    assert.equal(element('appShell').inert,false);
    assert.match(alerts[0],/Företagsbytet avbröts/);
    const writes=[];context.fetch=async(path,opts)=>{writes.push(JSON.parse(opts.body).name);return response();};
    await run('flushProfile()');assert.deepEqual(writes,['Unsaved']);
    """)


def test_minimal_health_is_not_mistaken_for_missing_api_key_and_logout_is_truthful():
    _node(r"""
    context.fetch=async()=>response({ok:true,version:'0.6.1'});
    await run('loadSystemStatus()');
    assert.equal(element('status').textContent,'System online · v0.6.1');
    context.fetch=async()=>response({detail:'offline'},false);
    await element('logout').onclick();
    assert.equal(navigations.length,0);
    context.fetch=async()=>response();await element('logout').onclick();
    assert.deepEqual(navigations,['reload']);
    """)


def test_failed_profile_save_does_not_prevent_session_logout():
    _node(r"""
    const calls=[];
    context.fetch=async(path)=>{
      calls.push(path);
      return path === '/api/auth/logout' ? response() : response({detail:'invalid profile'},false);
    };
    run("currentWorkspaceId=1; $('name').value=''; saveProfile();");
    await element('logout').onclick();
    assert.deepEqual(calls,['/api/company?workspace_id=1','/api/auth/logout']);
    assert.deepEqual(navigations,['reload']);
    """)
