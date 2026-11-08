# Vexmera: konkret testplan för privat beta

Plan upprättad: 2026-11-08. Ansvarig för genomförande och startbeslut: Erol.
Status: plan färdig; **NO-GO för ny extern onboarding** tills de återstående startkraven är verifierade. Detta är ett tekniskt nuläge, inte ett påstått godkännande från ägaren eller juridisk granskare.

## Omfattning

Börja med ett inbjudet företag och ett avgränsat läsflöde. Utöka därefter till 3–5 företag när första flödet är verifierat. Företagsnamn, kontaktpersoner och godkännanden registreras i den privata arbetsytan, inte i detta publika repository.

Piloten föreslås vara kostnadsfri och endast omfatta rapportering och beslutsstöd. Erol bekräftar upplägget före inbjudan. Använd bara leverantörer vars åtkomst har verifierats för det aktuella företaget. Instagram, Shopify eller LinkedIn ingår inte automatiskt bara för att anslutningens kod finns.

Inget i denna plan aktiverar annonser, publicering, budgetändringar, livebetalning eller nya behörigheter.

## Startkrav

| Krav | Bevis som krävs | Ansvarig |
| --- | --- | --- |
| Rätt produktionsversion | Vercel READY och exakt match mellan godkänd commit och `/health/runtime` | Teknisk ansvarig |
| Inloggad QA | Aktuell produktionssession, korrekt workspace, desktop och mobil, tydliga tom- och fellägen | Teknisk ansvarig + Erol |
| Företag och avgränsning | Ett företag har bekräftat deltagande, kontakt och vilka konton som får användas | Erol |
| Läsdata | Färsk synk och jämförelse av minst ett mått och en period mot källplattformen | Företagets kontoägare + teknisk ansvarig |
| Privacy och villkor | Faktisk avtalspart, verifierad kontakt, behandling/lagring och nödvändig avtalsgranskning | Erol + juridisk granskare |
| Säker drift | Extern exekvering och Autopilot låsta, ingen hemlighetsexponering eller tenantöverskridande åtkomst | Teknisk ansvarig |

Kör befintliga preflightverktyg i rätt operatörsmiljö. Den konsoliderade kontrollen använder en konservativ profil som även rapporterar Stripekrav. Dokumentera ett ej testat betalflöde separat. Ignorera inte ett fel genom att byta miljöflaggor eller märka en blockerad kontroll som godkänd.

## Genomförande

Dagarna räknas från faktiskt startbeslut, inte från dokumentets datum.

| Tidpunkt | Genomförande | Dokumenterat resultat |
| --- | --- | --- |
| Före start | Bekräfta samtliga startkrav och välj ett företag | Företagsreferens, datum, ansvarig och uttryckligt startbeslut |
| Dag 1 | Logga in, kontrollera workspace och färdigställ företagets profil | Onboarding fungerar och överlever omladdning |
| Dag 1–2 | Anslut godkänd källa och läs data för överenskommen period | Verifierat mått, period, datakälla och färskhetsdatum |
| Dag 2–3 | Låt användaren öppna Översikt, Core och Insikter samt identifiera nästa åtgärd | Relevans, begriplighet och observerad friktion |
| Dag 3–5 | Gör minst ett återbesök och kontrollera tom-/felläge utan att ändra externa konton | Tillförlitligt dataläge och begriplig återhämtning |
| Dag 5 | Samla feedback och besluta fortsätt, rätta eller stoppa | Lärdomar, blockerare, uppföljningsansvarig och nästa test |

## Mätbara framgångskriterier

Detta är föreslagna produktmål som Erol och pilotföretaget fastställer före start.

- Minst ett företag genomför det överenskomna läsflödet och ett återbesök.
- Minst ett rapportmått för samma datumintervall stäms av mot den anslutna källan. Skillnader förklaras innan resultatet används som bevis.
- Användaren kan hitta sin rapport och beskriva ett relevant nästa steg utan att uppgifterna framställs som publicerade eller genomförda.
- Användaren lämnar ett betyg 1–5 för begriplighet och nytta samt ett konkret förbättringsförslag. Förslaget till fortsättningsgräns är minst 4/5; ett lägre betyg ger en åtgärd och omtest.
- Inga öppna kritiska fel i åtkomst, tenantisolering, hemlighetshantering eller dataintegritet.
- Ingen extern annons-/butiksändring och ingen livebetalning utförs.

## Bevis och uppföljning

Återanvänd `PILOT_COMPANY_EVIDENCE_TEMPLATE.md` per företag. Håll kundidentitet och kunddata i den privata arbetsytan. Registrera commit, datum, testare, miljö, testflöde, jämförelse med källan, observerat resultat och PASS/BLOCKED/FAIL. Tomma mallar, äldre synkrader och syntetiska CI-konton är inte pilotbevis från ett verkligt företag.

För feedback: Vad blev tydligare? Vilken uppgift gick snabbare? Vad var svårt att lita på? Vilken förbättring behövs först?

Vid problem: registrera reproduktionssteg, förväntat och faktiskt resultat, prioritet, ansvarig och omtest på en identifierad version. Fortsätt inte onboarda om ett stoppvillkor i `FIVE_COMPANY_PILOT_RUNBOOK.md` utlöses.

## Betalning och frivilliga anslutningar

- Ett kostnadsfritt lästest är inte ett godkännande att starta betald self-service.
- Stripeportalens kompletta testtur och korrekt konto/priskatalog verifieras separat före betalstart. Befintliga applikationsspärrar behålls.
- Shopify och LinkedIn kräver sina faktiska appkonfigurationer; Instagram kräver godkänd professionell kontoåtkomst. Ett utelämnat, icke efterfrågat pilotflöde markeras N/A, inte verifierat.
- Startbeslut och vald omfattning sparas i veckoplanen. Kopiera veckoplanen och behåll föregående veckas låsta historik.
