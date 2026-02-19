"""
SUPPORT STARTER AI - LOCAL FALLBACK MODEL
==========================================
Rule-based responses for simple queries - no LLM needed
"""

from typing import Optional, Dict, List, Tuple
import re


class LocalModel:
    """
    Rule-based model for handling simple queries without calling external APIs.
    Much faster and free for common questions.
    """
    def __init__(self, company_name: str = "Vallhamragruppen AB"):
        self.company_name = company_name

        # Simple query patterns with direct responses
        self.patterns = {
            # ============================================
            # CONTACT & LOCATION
            # ============================================
            r"\b(kontakt|telefon|ring|nummer|phone|call)\b": {
                "response": "Ring oss på 0793-006638 eller mejla info@vallhamragruppen.se. Vi finns i Johanneberg, Partille och Mölndal.",
                "intent": "contact",
                "lead_score": 1
            },
            r"\b(adress|plats|var|var finns ni|hitta)\b": {
                "response": "Vi verkar i Johanneberg, Partille och Mölndal. Kontakt: 0793-006638, info@vallhamragruppen.se",
                "intent": "location",
                "lead_score": 1
            },
            r"\b(öppettider|när är ni öppna|öppet|öppettid|hours)\b": {
                "response": "Mån-Fre 08:00-17:00. Akuta ärenden: ring jour på 0793-006638.",
                "intent": "hours",
                "lead_score": 1
            },
            r"\b(email|e-post|mejla|mail|adress)\b": {
                "response": "info@vallhamragruppen.se",
                "intent": "email",
                "lead_score": 1
            },

            # ============================================
            # GREETINGS & SOCIAL
            # ============================================
            r"\b(hej|tjena|hallå|god dag|hello|hi|hey|godmorgon|godkväll|morsan|påsnor)\b": {
                "response": "Hej! Vallhamragruppen här. Vad kan jag hjälpa med?",
                "intent": "greeting",
                "lead_score": 1
            },
            r"\b(tack|tackar|tacksam|thanks|thank|tack så mycket|snälla)\b": {
                "response": "Varsågod! Fler frågor - bara fråga.",
                "intent": "gratitude",
                "lead_score": 1
            },
            r"\b(hejdå|adjö|vi ses|bye|goodbye|ha det så|seeya)\b": {
                "response": "Ha en bra dag!",
                "intent": "goodbye",
                "lead_score": 1
            },

            # ============================================
            # FAULT REPORTS - GENERAL
            # ============================================
            r"\b(felanmälan|felanmäl|anmäl fel|reparation|problem|fungerar inte|broken|issue)\b": {
                "response": "Felanmälan: ring 0793-006638 eller använd formulär på hemsidan. Akuta ärenden prioriteras.",
                "intent": "technical_issue",
                "lead_score": 2
            },

            # ============================================
            # WATER & PLUMBING
            # ============================================
            r"\b(översvämning|vattenläcka.*(akut|stort|forsar)|brustet.*rör|står.*vatten|forsar.*vatten|emergency|flood)\b": {
                "response": "Vattenläcka - stäng av vattnet under diskhon. Ring jour 0793-006638 direkt. Var läcker det?",
                "intent": "water_critical",
                "lead_score": 2
            },
            r"\b(droppar|läcker|kran|diskmaskin|tvättmaskin|avlopp|tolett|wc|vatten)\b": {
                "response": "Vattenproblem. Läcka eller droppande kran? Var i lägenheten? Är det farligt för el eller golv? Ring 0793-006638.",
                "intent": "water_question",
                "lead_score": 2
            },
            r"\b(avlopp|stopp|propp|backar|tömmer.*inte|luktar.*ill|avlopps|avloppsproblem)\b": {
                "response": "Avloppsproblem. Har du provat rensa själv? Gäller det kök eller badrum? Ring 0793-006638.",
                "intent": "drainage",
                "lead_score": 2
            },
            r"(avloppet.*stopp|stopp.*avlopp|propp.*avlopp|avlopp.*propp|avloppet.*backar)": {
                "response": "Avloppsproblem. Har du provat rensa själv? Gäller det kök eller badrum? Ring 0793-006638.",
                "intent": "drainage",
                "lead_score": 2
            },
            r"(inget.*vatten|vatten.*slutar|kranen.*ger|inget.*kommer)": {
                "response": "Inget vatten. Gäller det hela fastigheten eller bara din lägenhet? Kolla med grannen. Ring 0793-006638 om det inte återkommer.",
                "intent": "no_water",
                "lead_score": 2
            },
            r"\b(värmepanna|vattenberedare|beredare|varmvatten|varmvattentank)\b": {
                "response": "Problem med varmvatten? Kolla om den eldrivna beredaren har ström. Gasol? Behöver påfyllning. Ring 0793-006638.",
                "intent": "water_heater",
                "lead_score": 2
            },
            r"\b(badrumsrenovering|katsbyggnation|rot|renovera.*badrum)\b": {
                "response": "Renovering av våtrum kräver bygglov och certifierad firma. Är detta planerat eller akut? Ring 0793-006638 för råd.",
                "intent": "renovation",
                "lead_score": 3
            },

            # ============================================
            # KEYS, LOCKS & SECURITY
            # ============================================
            r"\b(tappat.*nyckel|nyckel.*borta|glömde.*nyckel|utelåst|låst.*ute|kommer.*inte.*in|kan.*ej.*komma|låset.*går.*inte)\b": {
                "response": "Utelåst? Ring jour 0793-006638 nu. Vilken adress?",
                "intent": "lockout_critical",
                "lead_score": 2
            },
            r"\b(nyckel|lås|dörr|låset|nyckelkort|tagg|passage)\b": {
                "response": "Nyckel- eller låsproblem. Tappad nyckel eller trasigt lås? Ring 0793-006638.",
                "intent": "lock_question",
                "lead_score": 2
            },
            r"\b(inbrott|skadegörelse|krossat|försöker.*ta.*sig|klotter|grafitti|vandalism)\b": {
                "response": "Inbrott eller skadegörelse? Ring polisen på 114 14 först. Anmäl sedan till oss på 0793-006638 för dokumentation.",
                "intent": "security_incident",
                "lead_score": 3
            },
            r"\b(larm| BRANDLARM|brandvarnare|larmar| tjut|pieper)\b": {
                "response": "Larmar brandvarnarna utan brand? Ventilera eller flytta den. Ej brand? Ring 0793-006638 för teknisk hjälp.",
                "intent": "alarm",
                "lead_score": 2
            },

            # ============================================
            # HEATING & VENTILATION
            # ============================================
            r"\b(ingen värme|kallt|fryser|elementen|element fungerar|dricks inte|inget varmt|det är kallt|kyla|elementen ej|värme ej)\b": {
                "response": "Ingen värme. Kollat termostaten på elementen? Gäller ett element eller hela lägenheten? Ring 0793-006638.",
                "intent": "heating_issue",
                "lead_score": 2
            },
            r"\b(ventilation|fläkt|spiskåpa|badrumsfläkt|fläktar|luktar|fukt|mögel|fuktig)\b": {
                "response": "Ventilationsproblem. Kolla att ventilationsdonen är öppna. Rengjorda nyligen? Ring 0793-006638.",
                "intent": "ventilation",
                "lead_score": 2
            },
            r"\b(golvvärme|golvvärme|termostat|golv)\b": {
                "response": "Golvvärmeproblem? Kolla termostaten - felkod? Ring 0793-006638 med felkod om möjligt.",
                "intent": "floor_heating",
                "lead_score": 2
            },
            r"\b(fjärrvärme|värmeväxlare| radiator|elementljud|klick|slår|bänkar)\b": {
                "response": "Fjärrvärme/elementproblem. Klickande eller kalla element? Lufta om det behövs. Ring 0793-006638.",
                "intent": "heating_system",
                "lead_score": 2
            },

            # ============================================
            # ELECTRICITY
            # ============================================
            r"\b(ingen ström|strömavbrott|slut|inte fungerar|mörkt|ljuset fungerar ej|elektricitet|el av|avbrott)\b": {
                "response": "Strömproblem. Kolla säkringsskärmet i trapphus först. Gäller hela lägenheten? Ring 0793-006638.",
                "intent": "electric_issue",
                "lead_score": 2
            },
            r"\b(säkring|säkringar|propp|skurmat|elektriker|elavbrott|glimmar|blinkar)\b": {
                "response": "Elproblem. Kolla säkringsskärmet i trapphus. Har skurmat? Gäller en krets eller allt? Ring 0793-006638.",
                "intent": "electrical",
                "lead_score": 2
            },
            r"\b(ljuskälla|lampa|belysning|taklampa|spot|led|glödlampa)\b": {
                "response": "Belysningproblem. Glödlampa byter du själv. Armaturfel? Ring 0793-006638.",
                "intent": "lighting",
                "lead_score": 1
            },

            # ============================================
            # APPLIANCES & WHITE GOODS
            # ============================================
            r"\b(diskmaskin|tvättmaskin|torktumlare|kyl|frys|spis|ugn|häll|vitvaror)\b": {
                "response": "Vitvaror. Köpt av dig eller ingår i fastigheten? Ring 0793-006638.",
                "intent": "appliance",
                "lead_score": 2
            },
            r"\b(gått sönder|trasig sönder|tras|sönder|tillbörd sönder|har gått sönder|fungerar ej|dött)\b": {
                "response": "Gått sönder. Vad har hänt? Är det farligt? Ring 0793-006638.",
                "intent": "damaged_item",
                "lead_score": 2
            },
            r"\b(garanti|reklamation|byta|byter|ersätt)\b": {
                "response": "Garantifråga. Vad gäller? Köpt av dig eller ingår i avtal? Ring 0793-006638.",
                "intent": "warranty",
                "lead_score": 2
            },

            # ============================================
            # WINDOWS, DOORS & STRUCTURE
            # ============================================
            r"\b(fönster|fönsterbräda|karm|brott|spricka|läcker|insläpp|dra|dragit)\b": {
                "response": "Fönsterproblem. Krossat eller spricka? Kallt? Ring 0793-006638.",
                "intent": "window",
                "lead_score": 2
            },
            r"\b(dörr|pärm|balkongdörr|entré|ytterdörr|innerdörr|klo|gångjärn|slå|klnnar)\b": {
                "response": "Dörrproblem. Vilken dörr? Sitter fast eller går ej igen? Ring 0793-006638.",
                "intent": "door",
                "lead_score": 2
            },
            r"\b(balkong|terrass|uteplats|räcke|golv|rötta|lasering)\b": {
                "response": "Balkong/uteplats. Vad är problemet? Säkert? Ring 0793-006638.",
                "intent": "balcony",
                "lead_score": 2
            },
            r"\b(tak|takläck|läcker.*igenom|vatten.*tak|innanför|regnvatten)\b": {
                "response": "Takläcka. Akut! Placera hink under. Ring jour 0793-006638 direkt.",
                "intent": "roof_leak",
                "lead_score": 3
            },
            r"\b(golv|parkett|klinker|kakel|golvbräda|knarr|squeak|spricka)\b": {
                "response": "Golvproblem. Knarr, spricka eller fukt? Ring 0793-006638.",
                "intent": "floor",
                "lead_score": 2
            },
            r"\b(vägg|tapet|målning|färg|spricka|bubbla|flagor)\b": {
                "response": "Väggproblem. Sprickor eller fukt? Ring 0793-006638.",
                "intent": "wall",
                "lead_score": 2
            },
            r"\b(källare|krypgrund|fukt|mögel|lukt|illaluktande)\b": {
                "response": "Fukt/mögel? Allvarligt. Ring 0793-006638 direkt för besiktning.",
                "intent": "moisture",
                "lead_score": 3
            },

            # ============================================
            # PEST CONTROL
            # ============================================
            r"\b(skadedjur|råtta|rattor|mus| möss|kackerlack|kackerlackor|myra|myror|geting|getingar|vessel|vägglus|löss|bedbugs)\b": {
                "response": "Skadedjur? Ring 0793-006638. Vi ordnar sanering genom anticimex.",
                "intent": "pest",
                "lead_score": 2
            },
            r"\b(katt|hund|sällskapsdjur|djurhållning|husdjur)\b": {
                "response": "Djurfråga. Vad gäller? Regler eller problem? Ring 0793-006638.",
                "intent": "pets",
                "lead_score": 2
            },

            # ============================================
            # WASTE & RECYCLING
            # ============================================
            r"\b(soptunna|avfall|återvinning|träpunkten|grovsopor|kast|släng|tömning)\b": {
                "response": "Sopor/återvinning. Källa.se eller din kommun för tider. Behållproblem? Ring 0793-006638.",
                "intent": "waste",
                "lead_score": 1
            },
            r"\b(städning|städ|trappstädning|gemensam.*lokal|lokaluthyrning)\b": {
                "response": "Städfråga. Trappstädning ingår oftast. Ring 0793-006638.",
                "intent": "cleaning",
                "lead_score": 1
            },

            # ============================================
            # PARKING & CARS
            # ============================================
            r"\b(parkering|parker|garage|carport|bil|parkeringsplats|p-plats|laddstolpe|elbil)\b": {
                "response": "Parkering/garage. Vad gäller? Plats, laddstolpe eller port? Ring 0793-006638.",
                "intent": "parking",
                "lead_score": 2
            },
            r"\b(felställt|brott|inbrott.*bil|skadegörelse|vindruta|däck)\b": {
                "response": "Skadegörelse på fordon? Ring polisen 114 14. Anmäl till oss på 0793-006638.",
                "intent": "vehicle_damage",
                "lead_score": 2
            },

            # ============================================
            # GARDEN & OUTDOOR
            # ============================================
            r"\b(trädgård|gräsmatta|gräsklippning|snö|snöröjning|halka|halkbekämpning|sandning)\b": {
                "response": "Uteområde. Snöröjning/trädgård ingår ofta. Vad gäller? Ring 0793-006638.",
                "intent": "outdoor",
                "lead_score": 2
            },
            r"\b(grönområde| häck|buske|träd|beskärning|fallande|grenar)\b": {
                "response": "Grönyta. Beskärning eller farliga träd? Ring 0793-006638.",
                "intent": "garden",
                "lead_score": 2
            },
            r"(vem.*snöröjning|vem.*ansvarar.*snö|vem.*halka|halkbekämpning|sandning)": {
                "response": "Snöröjning och halkbekämpning ansvarar fastighetsägaren för på gemensamma ytor och entréer. Ring 0793-006638.",
                "intent": "snow_responsibility",
                "lead_score": 2
            },
            r"(vem.*ansvarar|vems.*ansvar|vem.*betalar|vem.*gör|vem.*sköter)": {
                "response": "Ansvarsfråga. Vad gäller specifikt? Ring 0793-006638 för besked.",
                "intent": "responsibility",
                "lead_score": 2
            },
            r"(vad.*ingår|ingår.*i|ingår.*förvaltning|vad.*ingår.*i.*förvaltning)": {
                "response": "Förvaltning ingår: drift och underhåll, ekonomisk förvaltning, hyresadministration. Ring 0793-006638.",
                "intent": "services",
                "lead_score": 2
            },
            r"(vembyter|vem.*byter|vem.*skall.*byter|vem.*ska.*byter|byter.*glödlampa|glödlampa)": {
                "response": "Hyresgäst/ägare byter självvanliga glödlampor. Armaturfel är fastighetsägarens ansvar. Ring 0793-006638.",
                "intent": "lighting_responsibility",
                "lead_score": 2
            },
            r"(hur.*luftrar|luftra.*element|lufta.*radiator|element.*lufta)": {
                "response": "Lufta element: Vänta tills det är varmt. Använd nyckel på sidan av elementet - vrid tills vatten kommer. Stäng till.",
                "intent": "radiator_airing",
                "lead_score": 2
            },
            r"(andra.*hand|andrahand|andrahands|hyra.*ut|andra.*hand.*hyra)": {
                "response": "Andrahandsuthyrning kräver godkännande. Kontakta oss på 0793-006638 för ansökan.",
                "intent": "sublet",
                "lead_score": 3
            },

            # ============================================
            # TENANT & LANDLORD RESPONSIBILITIES
            # ============================================
            r"\b(hyresgäst|hyresgästen|tvätta|tvättstuga|tvättid|boka.*tvätt)\b": {
                "response": "Hyresgästfråga. Tvättstuga? Kontakta firstname.lastname@example.com eller ring 0793-006638.",
                "intent": "tenant",
                "lead_score": 2
            },
            r"\b(hyra|hyresavi|hyreshöjning|förhandla|hyresnämnd)\b": {
                "response": "Hyresfråga. Vad gäller? Hyresnivå eller betalning? Ring 0793-006638.",
                "intent": "rent",
                "lead_score": 3
            },
            r"\b(andrahand|andra hand|andrahandsuthyrning|hyra ut|bostad)\b": {
                "response": "Andrahand? Kontakta oss på 0793-006638 för ansökan om andrahandsuthyrning.",
                "intent": "sublet",
                "lead_score": 3
            },
            r"\b(flytt|utflytt|inflytt|flyttstädn|nyckelavl)\b": {
                "response": "Flytt? Kontakta oss på 0793-006638 för flyttanmälan och nyckelöverlämning.",
                "intent": "moving",
                "lead_score": 3
            },
            r"\b(husordning|regler|stadgar|ordningsregler|föreskrifter)\b": {
                "response": "Regler? Vad gäller specifikt? Ring 0793-006638 så hjälper vi dig.",
                "intent": "rules",
                "lead_score": 1
            },
            r"\b(störning|stör|oljud|höga ljud|fest|musik|granne|grannar)\b": {
                "response": "Störning? Akut nattstörning: ring jour på 0793-006638. Dagtid: ring 0793-006638.",
                "intent": "disturbance",
                "lead_score": 2
            },
            r"\b(rökning|rök|rökfri|rygga|e-cigaret|vaping)\b": {
                "response": "Rökfråga. Regler varierar. Ring 0793-006638.",
                "intent": "smoking",
                "lead_score": 1
            },

            # ============================================
            # PROPERTY MANAGEMENT TERMS
            # ============================================
            r"\b(fastighetsförvaltning|förvaltning|förvaltare|fastighetsskötare|vaktmästare)\b": {
                "response": "Förvaltning: drift och underhåll, ekonomisk förvaltning, hyresadministration. Ring 0793-006638.",
                "intent": "management",
                "lead_score": 2
            },
            r"\b(drift|underhåll|skötsel|fastighetsdrift|driftkostnad)\b": {
                "response": "Drift & underhåll ingår i vår förvaltning. Specifik fråga? Ring 0793-006638.",
                "intent": "maintenance",
                "lead_score": 2
            },
            r"\b(ekonomi|bokslut|budget|årsredovisning|faktura|betalning|invoice)\b": {
                "response": "Ekonomifråga. Faktura eller betalning? Ring 0793-006638.",
                "intent": "finance",
                "lead_score": 3
            },
            r"\b(underhållsplan|besiktning|reparation|renovering| ROT|avhjälpande)\b": {
                "response": "Underhållsplan/Besiktning. Vad gäller? Ring 0793-006638.",
                "intent": "maintenance_plan",
                "lead_score": 3
            },
            r"\b(försäkring|försäkringsbolag|skada|anmäl skada|stöld|brand)\b": {
                "response": "Försäkring. Skadan på fastigheten eller din egendom? Ring 0793-006638.",
                "intent": "insurance",
                "lead_score": 3
            },
            r"\b(energi|energideklaration|energiklass|värmeisolering|energispar)\b": {
                "response": "Energifråga. Deklaration eller sparåtgärder? Ring 0793-006638.",
                "intent": "energy",
                "lead_score": 2
            },
            r"\b(brf|bostadsrätt|bostadsrättsförening|förening|styrelse|stämman|årsmöte)\b": {
                "response": "Bostadsrättsförening. Styrelsefråga - kontakta styrelsen. Förvaltningsfråga? Ring 0793-006638.",
                "intent": "brf",
                "lead_score": 3
            },
            r"\b(kommersiell|lokal|kontor|butik|lager|industri|företagslokal)\b": {
                "response": "Kommersiell lokal. Vad gäller? Hyra eller skötsel? Ring 0793-006638.",
                "intent": "commercial",
                "lead_score": 3
            },

            # ============================================
            # GENERAL COMPANY INFO
            # ============================================
            r"\b(vem är ni|vilka är ni|om företaget|bolaget|company| Vad gör ni)\b": {
                "response": f"{company_name} förvaltar fastigheter - drift, underhåll, ekonomi och hyresadministration för bostadsrättsföreningar och kommersiella fastigheter.",
                "intent": "about",
                "lead_score": 1
            },
            r"\b(tjänster|gör ni|erbjuder|service|services|Help)\b": {
                "response": "Fastighetsförvaltning: drift och underhåll, ekonomisk förvaltning, hyresadministration, projektledning.",
                "intent": "services",
                "lead_score": 2
            },

            # ============================================
            # BOOKING & MEETINGS
            # ============================================
            r"\b(boka|bokning|möte|visning|träff|meeting|book|appointment)\b": {
                "response": "Boka möte: ring 0793-006638 eller info@vallhamragruppen.se. När passar?",
                "intent": "booking_request",
                "lead_score": 5
            },
            r"\b(pris|kostar|kostnad|betala|price|pricing|how much|taxa|debitering)\b": {
                "response": "Pris sätts individuellt efter fastighet och tjänsteomfattning. Offert? Ring 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 3
            },
            r"\b(offert|offer|quote|prislista|price list|anbud)\b": {
                "response": "Kostnadsfri offert. Berätta om fastigheten så hjälper vi dig. Ring 0793-006638.",
                "intent": "pricing_question",
                "lead_score": 4
            },
            # Available apartments/properties
            r"\b(ledig|lediga|ledigt|tom|tomma|lägenhet|lägenheter|bostad|bostäder|fastighet|hyresrätt|brf|lokaler|lokal)\b": {
                "response": "Lediga lägenheter/lokaler? Kontakta oss på 0793-006638 eller info@vallhamragruppen.se så berättar vi vad du söker.",
                "intent": "availability",
                "lead_score": 4
            },

            # ============================================
            # NEGATIVE SENTIMENT & ESCALATION
            # ============================================
            r"\b(arg|förbannad|dålig|terrible|horrible|hate|ilsk|rasande|förbann)\b": {
                "response": "Jag förstår. Ring 0793-006638 så hjälper en kollega dig direkt.",
                "intent": "complaint",
                "lead_score": 1
            },
            r"\b(chef|manager|ledning|överordnad|mänsklig|human|person|prata med|tala med|komma fram|högre upp)\b": {
                "response": "Självklart. Ring 0793-006638 så hjälper vi dig.",
                "intent": "escalation_demand",
                "lead_score": 1
            },
            r"\b(klagomål|klaga|missnöjd|inte nöjd|dåligt|fungerar ej|skämt|skräpa)\b": {
                "response": "Jag beklagar. Ring 0793-006638 så hjälper vi dig direkt.",
                "intent": "complaint",
                "lead_score": 2
            },

            # ============================================
            # TIME & SCHEDULE
            # ============================================
            r"\b(när|hur länge|tid|vecka|dag|idag|imorgon|snarast|skynda)\b": {
                "response": "Tidsfråga. Vad gäller? Akut ärenden hanteras direkt. Övriga: ring 0793-006638.",
                "intent": "timing",
                "lead_score": 1
            },
            r"\b(vänta|kö|ledtid|handläggningstid)\b": {
                "response": "Väntetid? Vad är ärendet? Akut prioriteras. Ring 0793-006638 för status.",
                "intent": "wait_time",
                "lead_score": 1
            },

            # ============================================
            # SEASONAL SPECIFIC
            # ============================================
            r"\b(vinter| snö|is| halka|kyla|element| frost|värme)\b": {
                "response": "Vinterfrågor? Snöröjning/halkbekämpning ingår ofta. Värmeproblem? Ring 0793-006638.",
                "intent": "seasonal",
                "lead_score": 2
            },
            r"\b(sommar|värme|svala|通风|fläkt|gräsklipp)\b": {
                "response": "Sommarfrågor? Ventilation eller grönyta? Ring 0793-006638.",
                "intent": "seasonal",
                "lead_score": 2
            },

            # ============================================
            # TECHNICAL TERMS
            # ============================================
            r"\b(felanmälanssystem|app|portal|inlogg|lös|ord|mitt|konto|min sida)\b": {
                "response": "Systemfråga. Felanmälan via hemsida eller ring 0793-006638. Inloggningsproblem? Ring 0793-006638.",
                "intent": "system",
                "lead_score": 1
            },
            r"\b(lorem|ipsum|test|demo|exempel)\b": {
                "response": "Testmeddelande mottaget. Kontakta oss på 0793-006638 för riktiga ärenden.",
                "intent": "test",
                "lead_score": 1
            },
        }

    def can_handle(self, message: str) -> bool:
        """Check if this message can be handled by local model"""
        message_lower = message.lower()

        # Check each pattern
        for pattern in self.patterns.keys():
            if re.search(pattern, message_lower):
                return True

        return False

    def generate(self, message: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate a response using local rules

        Returns:
            Dict with: response, intent, confidence, lead_score, escalate
        """
        message_lower = message.lower()

        # Check each pattern (more specific first)
        for pattern, data in self.patterns.items():
            if re.search(pattern, message_lower):
                return {
                    "response": data["response"],
                    "intent": data["intent"],
                    "confidence": 0.85,  # High confidence for pattern matches
                    "lead_score": data["lead_score"],
                    "escalate": data["intent"] in ["complaint", "escalation_demand"]
                }

        # Fallback - check for common words to provide better response
        fallback_check = {
            r"(vem|vad|vilken|vilket|vilka|hur|var|när|varför)": "Jag hjälper med frågor om fastigheter, felanmälan, förvaltning, bokning med mera. Ring 0793-006638 eller beskriv ditt ärende.",
            r"(problem|fel|felanmälan|hjälp|störd|skad)":
                "Beskriv problemet så hjälper jag dig. Felanmälan når du på 0793-006638.",
            r"(snöröjning|halka|is|snö|vinter)":
                "Snöröjning och halkbekämpning ingår för gemensamma ytor. Egna uppgifter sköter du själv. Ring 0793-006638.",
            r"(lås|nyckel|dörr|öppna|lås|byte|byt)":
                "Lås- eller nyckelproblem? Ring 0793-006638.",
        }

        for pattern, response in fallback_check.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "response": response,
                    "intent": "general",
                    "confidence": 0.5,
                    "lead_score": 1,
                    "escalate": False
                }

        return {
            "response": "Berätta vad du behöver hjälp med så ska jag göra mitt bästa. Du kan också ringa 0793-006638.",
            "intent": "unknown",
            "confidence": 0.3,
            "lead_score": 1,
            "escalate": False
        }

    def is_simple_query(self, message: str) -> bool:
        """Quick check if this is a simple query we can handle"""
        return self.can_handle(message)


class HybridBot:
    """
    Hybrid bot that uses local model for simple queries
    and falls back to LLM for complex ones
    """
    def __init__(self, local_model: LocalModel, anthropic_client=None):
        self.local_model = local_model
        self.anthropic_client = anthropic_client

    def generate(self, message: str, system_prompt: str, context: Optional[Dict] = None) -> Dict:
        """
        Generate response using best available model

        Args:
            message: User message
            system_prompt: System prompt for LLM
            context: Optional conversation context

        Returns:
            Dict with response and metadata
        """
        # Try local model first for simple queries
        if self.local_model.is_simple_query(message):
            return self.local_model.generate(message, context)

        # Fall back to Anthropic for complex queries
        if self.anthropic_client:
            try:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.4,
                    system=system_prompt,
                    messages=[{"role": "user", "content": message}]
                )

                return {
                    "response": response.content[0].text,
                    "intent": "complex",
                    "confidence": 0.9,
                    "lead_score": 2,
                    "escalate": False
                }
            except Exception as e:
                print(f"LLM Error: {e}")

        # Final fallback
        return self.local_model.generate(message, context)


# Pre-configured instance
_default_local_model: Optional[LocalModel] = None


def get_local_model(company_name: str = "Vallhamragruppen AB") -> LocalModel:
    """Get or create default local model instance"""
    global _default_local_model
    if _default_local_model is None:
        _default_local_model = LocalModel(company_name)
    return _default_local_model


if __name__ == "__main__":
    # Test the local model
    print("=" * 60)
    print("LOCAL MODEL - TEST")
    print("=" * 60)

    model = LocalModel()

    test_queries = [
        "Hej!",
        "Hur gör jag en felanmälan?",
        "Vad är er adress?",
        "Hur mycket kostar det?",
        "Jag vill boka ett möte",
        "Tack!",
        "Det här är hemskt!"
    ]

    for query in test_queries:
        result = model.generate(query)
        print(f"\nQ: {query}")
        print(f"A: {result['response']}")
        print(f"   Intent: {result['intent']}, Confidence: {result['confidence']}, Lead: {result['lead_score']}")
