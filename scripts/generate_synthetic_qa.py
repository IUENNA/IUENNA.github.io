#!/usr/bin/env python3
"""
generate_synthetic_qa.py
-------------------------
Generates an extensive, scientifically vetted synthetic Q&A corpus
based on authoritative research data (data/iuenna_grundlagen.md), ARCHE collections,
and Knowledge Graph nodes.

Outputs:
  1. data/iuenna_synthetic_qa.json      -> Formatted for the client-side chat matcher & Qwen 2.5 context
  2. data/iuenna_finetune_alpaca.json    -> Instruction-tuning dataset in Alpaca format (instruction, input, output)
  3. data/iuenna_finetune_sharegpt.json  -> Multi-turn format for ChatML / ShareGPT
  4. data/iuenna_finetune_chatml.jsonl   -> Line-delimited JSON for Hugging Face / Unsloth fine-tuning
"""

import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

QA_OUTPUT_FILE = os.path.join(DATA_DIR, "iuenna_synthetic_qa.json")
ALPACA_OUTPUT_FILE = os.path.join(DATA_DIR, "iuenna_finetune_alpaca.json")
SHAREGPT_OUTPUT_FILE = os.path.join(DATA_DIR, "iuenna_finetune_sharegpt.json")
JSONL_OUTPUT_FILE = os.path.join(DATA_DIR, "iuenna_finetune_chatml.jsonl")

SYNTHETIC_CORPUS = [
    # -------------------------------------------------------------
    # 1. NEUBEWERTUNG & TOPOGRAFIE (Tscherberg, Globasnitz, Vicus)
    # -------------------------------------------------------------
    {
        "id": "qa_tscherberg_neubewertung",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Ist Globasnitz wirklich die römische Straßenstation Iuenna?",
        "variations": [
            "War Globasnitz die römische Straßenstation Iuenna?",
            "Wo lag die Straßenstation Iuenna wirklich?",
            "Warum ist die Gleichsetzung von Globasnitz mit Iuenna umstritten?",
            "Ist Iuenna und Globasnitz derselbe Ort?",
            "Liegt Iuenna in Globasnitz?",
            "Iuenna Tscherberg Hypothese"
        ],
        "answer": "Die neuere archäologische Gesamtauswertung (Christian Gugl et al.) stellt die traditionelle Gleichsetzung infrage. Globasnitz war ein etwa 7–9 ha großer, nichtstädtischer vicus, lag jedoch mehr als drei Kilometer südlich der römischen Hauptstraße Celeia–Virunum. Als wahrscheinlichere Lage der Straßenstation Iuenna wird heute Tscherberg vorgeschlagen, da dieser Ort direkt an der Haupttrasse liegt und mit der auf der Tabula Peutingeriana genannten Distanz von 23 römischen Meilen ab Virunum übereinstimmt. Globasnitz selbst war demnach ein vicus unbekannten antiken Namens.",
        "citations": ["Christian Gugl et al.", "Ladstätter (2000)", "Hagmann & Reiner (2023)"],
        "keywords": ["globasnitz", "iuenna", "tscherberg", "straßenstation", "mansio", "vicus", "celeia", "virunum", "tabula peutingeriana", "neubewertung", "gugl"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_tscherberg_rolle",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Welche Rolle spielt Tscherberg in der neuesten Iuenna-Forschung?",
        "variations": [
            "Was hat Tscherberg mit Iuenna zu tun?",
            "Warum wird Tscherberg als Iuenna lokalisiert?",
            "Liegt die Straßenstation Iuenna bei Tscherberg?",
            "Tscherberg Straßenstation"
        ],
        "answer": "Tscherberg wird in der jüngsten Synthese (Christian Gugl et al.) als alternative und plausiblere Lokalisierung der Straßenstation Iuenna vorgeschlagen. Tscherberg lag unmittelbar an der römischen Hauptverkehrsachse Virunum–Celeia, zeigt archäologische Hinweise auf römerzeitliche Bebauung und passt exakt zu den 23 Meilen der Tabula Peutingeriana. Die spätantike Höhensiedlung auf dem Katharinakogel könnte dessen befestigte Nachfolgesiedlung darstellen.",
        "citations": ["Christian Gugl et al."],
        "keywords": ["tscherberg", "iuenna", "straßenstation", "haupttrasse", "virunum", "celeia", "katharinakogel", "tabula peutingeriana"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_katharinakogel_bedeutung",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Was befand sich auf dem Katharinakogel und wie hängt er mit Iuenna zusammen?",
        "variations": [
            "Welche Rolle spielt der Katharinakogel?",
            "Was war die Befestigung auf dem Katharinakogel?",
            "Katharinakogel Höhensiedlung"
        ],
        "answer": "Auf dem Katharinakogel befand sich eine spätantike Befestigung. Nach den neuesten topografischen Erkenntnissen (Christian Gugl et al.) wird der Katharinakogel als befestigte Nachfolgesiedlung der bei Tscherberg vermuteten Straßenstation Iuenna interpretiert, analog zur Verlagerung von Talsiedlungen auf befestigte Höhenzüge in der Spätantike.",
        "citations": ["Christian Gugl et al."],
        "keywords": ["katharinakogel", "spätantike", "befestigung", "höhensiedlung", "tscherberg", "nachfolgesiedlung", "iuenna"],
        "graph_node_id": "col_1792417"
    },
    {
        "id": "qa_vicus_globasnitz_groesse",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Wie groß war die römische Siedlung (vicus) in Globasnitz?",
        "variations": [
            "Wie groß war der vicus von Globasnitz?",
            "Ausdehnung römische Siedlung Globasnitz",
            "Geophysikalische Prospektion Globasnitz",
            "Wie groß ist das Siedlungsareal von Globasnitz?"
        ],
        "answer": "In vier Messkampagnen (2020–2023) wurden rund 21 Hektar geomagnetisch und ca. 4 Hektar mit Georadar prospektiert. Sie belegen für Globasnitz einen ca. 7–9 Hektar großen, nichtstädtischen vicus mit Nord-Süd-Straße im Ortszentrum, ummauerten Gebäudekomplexen und einer mindestens 400 Meter langen Gräberstraße mit aufwendigen Grabbezirken im Westen (Christian Gugl et al.; Schwaiger & Reiner 2022).",
        "citations": ["Christian Gugl et al.", "Schwaiger & Reiner (2022)"],
        "keywords": ["vicus", "globasnitz", "größe", "hektar", "prospektion", "georadar", "geomagnetik", "gräberstraße", "ausdehnung"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_entstehungsgruende_vicus_globasnitz",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Warum entstand die römische Siedlung in Globasnitz, wenn sie nicht an der Hauptstraße lag?",
        "variations": [
            "Warum gab es eine Siedlung in Globasnitz?",
            "Bedeutung von Globasnitz in der Römerzeit",
            "Kultische Anziehungskraft Hemmaberg Globasnitz"
        ],
        "answer": "Da Globasnitz abseits der Hauptstraße lag, werden andere Faktoren für seine Bedeutung diskutiert: Erstens die reichen umliegenden Landgüter lokaler und städtischer Eliten (wie St. Stefan), zweitens die Wegeverbindung über den Luschasattel über die Karawanken und drittens die kultische Anziehungskraft des Hemmabergs und der Rosaliengrotte (römerzeitliches Quellheiligtum und Kontinuität vom heidnischen Kultplatz zum christlichen Pilgerzentrum; Christian Gugl et al.; Ladstätter 2000).",
        "citations": ["Christian Gugl et al.", "Ladstätter (2000)"],
        "keywords": ["entstehung", "vicus", "globasnitz", "luschasattel", "landgüter", "quellheiligtum", "rosaliengrotte", "kultplatz"],
        "graph_node_id": "col_1792169"
    },

    # -------------------------------------------------------------
    # 2. VILLENANLAGE ST. STEFAN (Šteben)
    # -------------------------------------------------------------
    {
        "id": "qa_st_stefan_lage",
        "lang": "de",
        "category": "Villenanlage St. Stefan",
        "question": "Wo genau liegt die römische Villenanlage von St. Stefan?",
        "variations": [
            "Lage Villa St. Stefan",
            "Wo befindet sich die römische Villa in St. Stefan?",
            "Wie weit ist St. Stefan von Globasnitz entfernt?",
            "St. Stefan Steben Lage"
        ],
        "answer": "Die Villenanlage von St. Stefan (slowenisch Šteben) liegt rund 1,2 km nördlich des heutigen Ortskerns von Globasnitz im südlichen Jauntal (Christian Gugl et al.).",
        "citations": ["Christian Gugl et al.", "Schwaiger & Reiner (2022)"],
        "keywords": ["st. stefan", "šteben", "steben", "lage", "entfernung", "globasnitz", "nördlich", "jauntal"],
        "graph_node_id": "col_1792411"
    },
    {
        "id": "qa_st_stefan_architektur",
        "lang": "de",
        "category": "Villenanlage St. Stefan",
        "question": "Welche architektonischen Merkmale zeichnen die Villenanlage von St. Stefan aus?",
        "variations": [
            "Was ist über die Architektur der Villa St. Stefan bekannt?",
            "Befunde St. Stefan",
            "Super-Villa St. Stefan Ausstattung",
            "Hypokaust St. Stefan"
        ],
        "answer": "Die Villenanlage in St. Stefan umfasst ein prospektiertes Areal von rund 2 Hektar (bzw. 7.700 m² Kernzone) mit mindestens drei Bauphasen. Typologisch handelt es sich um eine im südlichen Noricum verbreitete Orthogonalanlage mit klarer funktionaler Trennung zwischen repräsentativem Wohnbereich (pars urbana) und landwirtschaftlichen Teilen (pars rustica). Sie besaß Hofmauern, einen Prunksaal mit zwei gegenüberliegenden Apsiden sowie ein eigenes Badegebäude mit Hypokaust-Fußbodenheizung und Wasserkanal (Christian Gugl et al.; Schwaiger & Reiner 2022).",
        "citations": ["Christian Gugl et al.", "Schwaiger & Reiner (2022)", "Hagmann & Reiner (2023)"],
        "keywords": ["st. stefan", "villa", "super-villa", "architektur", "orthogonalanlage", "apsiden", "hypokaust", "badegebäude", "wasserkanal"],
        "graph_node_id": "col_1792411"
    },
    {
        "id": "qa_barbius_vercaius",
        "lang": "de",
        "category": "Villenanlage St. Stefan",
        "question": "Wer war L. Barbius Vercaius und welche Bedeutung hat seine Grabinschrift in St. Stefan?",
        "variations": [
            "Barbius Vercaius",
            "Grabinschrift Pfarrkirche St. Stefan",
            "Virunenser Ädil St. Stefan",
            "Wer war L. Barbius Vercaius?"
        ],
        "answer": "L. Barbius Vercaius war ein ehemaliger Ädil (hoher städtischer Magistrat) der norischen Provinzhauptstadt Virunum. Seine Grabinschrift ist sekundär in der Pfarrkirche von St. Stefan verbaut. Dieser epigraphische Befund deutet darauf hin, dass die ausgedehnte Villenlandschaft um Globasnitz im Besitz von Angehörigen der städtischen Oberschicht und führenden Eliten Virunums stand (Christian Gugl et al.).",
        "citations": ["Christian Gugl et al."],
        "keywords": ["barbius vercaius", "virunum", "ädil", "magistrat", "grabinschrift", "pfarrkirche", "st. stefan", "elite", "grundbesitzer"],
        "graph_node_id": "col_1792411"
    },
    {
        "id": "qa_hans_winkler_skizzen",
        "lang": "de",
        "category": "Villenanlage St. Stefan",
        "question": "Welche Rolle spielten die historischen Skizzen von Hans Winkler bei der Erforschung von St. Stefan?",
        "variations": [
            "Hans Winkler Skizzen",
            "Hans Winkler Tagebücher",
            "Hans Winkler Badegebäude St. Stefan",
            "Wie halfen Hans Winklers Notizen bei St. Stefan?"
        ],
        "answer": "Hans Winkler führte bereits im frühen 20. Jahrhundert (u. a. 1930) Ausgrabungen in St. Stefan durch und dokumentierte eine Hypokaustheizung. Im Projekt IUENNA wurden seine handschriftlichen Skizzen und Tagebücher im kärnten.museum aufgespürt, retrodigitalisiert (Subcollection RET) und in ARCHE archiviert. Erst der digitale Abgleich dieser historischen Skizzen mit modernen Georadardaten ermöglichte es dem Forschungsteam, das Gebäude zweifelsfrei als römisches Badegebäude zu rekapitulieren (Christian Gugl et al.; Hagmann & Reiner 2023).",
        "citations": ["Christian Gugl et al.", "Hagmann & Reiner (2023)"],
        "keywords": ["hans winkler", "skizzen", "tagebuch", "retrodigitalisate", "ret", "st. stefan", "hypokaust", "badegebäude", "arche"],
        "graph_node_id": "col_1792572"
    },

    # -------------------------------------------------------------
    # 3. HEMMABERG & FRÜHCHRISTLICHE SAKRALTOPOGRAFIE
    # -------------------------------------------------------------
    {
        "id": "qa_hemmaberg_bedeutung",
        "lang": "de",
        "category": "Hemmaberg",
        "question": "Was ist der Hemmaberg und warum ist er archäologisch so berühmt?",
        "variations": [
            "Was ist der Hemmaberg?",
            "Bedeutung des Hemmabergs",
            "Warum ist der Hemmaberg wichtig?",
            "Frühchristliches Zentrum Hemmaberg",
            "Pilgerheiligtum Hemmaberg"
        ],
        "answer": "Der 843 m hohe Hemmaberg ist eine der am besten erforschten spätantiken Höhensiedlungen (ca. 5 ha) und das bedeutendste frühchristliche Pilgerzentrum im Südostalpenraum. Er besitzt mindestens fünf frühchristliche Kirchen (darunter monumentale Doppelkirchenanlagen des 6. Jhs.), reich verzierte Mosaikböden, Reliquienkammern unter den Altären, Grabräume für Kleriker und Stifter, ein Pilgerhospiz sowie die Rosaliengrotte (Ladstätter 2000; Hagmann & Reiner 2023).",
        "citations": ["Ladstätter (2000)", "Hagmann & Reiner (2023)"],
        "keywords": ["hemmaberg", "pilgerzentrum", "pilger", "doppelkirchen", "mosaike", "reliquien", "höhensiedlung", "rosaliengrotte", "ladstätter"],
        "graph_node_id": "col_1792212"
    },
    {
        "id": "qa_hemmaberg_doppelkirchen",
        "lang": "de",
        "category": "Hemmaberg",
        "question": "Warum gibt es auf dem Hemmaberg monumentale Doppelkirchen?",
        "variations": [
            "Doppelkirchen Hemmaberg",
            "Zwei Kirchen nebeneinander Hemmaberg",
            "Katholisch und arianisch Hemmaberg",
            "Gotische und romanische Gemeinde Hemmaberg"
        ],
        "answer": "Im frühen 6. Jahrhundert wurden auf dem Hemmaberg zwei parallele Kirchenanlagen errichtet. In der archäologischen Forschung (u. a. Sabine Ladstätter, Christian Gugl) wird dies als Koexistenz zweier getrennter christlicher Gemeinschaften interpretiert: einer katholisch-romanischen Provinzialbevölkerung und einer arianisch-gotischen Gemeinde unter ostgotischer Herrschaft. Jede Gemeinde verfügte über eigene Eucharistie- und Memorialkirchen sowie Taufbecken (Ladstätter 2000; Gugl et al.).",
        "citations": ["Ladstätter (2000)", "Christian Gugl et al."],
        "keywords": ["doppelkirche", "doppelkirchen", "hemmaberg", "arianisch", "katholisch", "ostgoten", "ladstätter", "taufbecken", "liturgie"],
        "graph_node_id": "col_1792212"
    },
    {
        "id": "qa_gottheit_iouenat",
        "lang": "de",
        "category": "Hemmaberg & Etymologie",
        "question": "Wer war die Gottheit Iouenat und woher stammt der Name Iuenna?",
        "variations": [
            "Wer war Iouenat?",
            "Gottheit Iouenat",
            "Woher kommt der Name Iuenna?",
            "Etymologie Jauntal Iuenna",
            "Votivaltar Hemmaberg Iouenat"
        ],
        "answer": "Iouenat war eine einheimische keltische Schutzgottheit, die auf dem Hemmaberg verehrt wurde. Ein dort entdeckter römischer Votivaltar belegt ihren Kult. Von der Gottheit Iouenat leitet sich der Name der römischen Siedlung bzw. Straßenstation Iuenna (Tabula Peutingeriana) ab, ebenso wie die heutigen geografischen Bezeichnungen Jaunberg und Jauntal (slowenisch Podjuna; Ladstätter 2000; Gugl et al.).",
        "citations": ["Ladstätter (2000)", "Christian Gugl et al."],
        "keywords": ["iouenat", "gottheit", "keltisch", "hemmaberg", "altar", "iuenna", "jaunberg", "jauntal", "podjuna", "etymologie"],
        "graph_node_id": "col_1792212"
    },
    {
        "id": "qa_hemmaberg_ende",
        "lang": "de",
        "category": "Hemmaberg",
        "question": "Wann und wie endete die antike Besiedlung auf dem Hemmaberg?",
        "variations": [
            "Wann endete der Hemmaberg?",
            "Ende der Siedlung Hemmaberg",
            "Wann wurde der Hemmaberg verlassen?",
            "Ende um 600 n. Chr."
        ],
        "answer": "Die Funde aus den Wohnbereichen und die Belegungsdauer der Gräberfelder auf dem Hemmaberg zeigen, dass die befestigte Höhensiedlung und das überregionale frühchristliche Pilgerzentrum um etwa 600 n. Chr. aufgegeben wurden (Ladstätter 2000; Gugl et al.).",
        "citations": ["Ladstätter (2000)", "Christian Gugl et al."],
        "keywords": ["ende", "aufgabe", "600", "spätantike", "hemmaberg", "besiedlung"],
        "graph_node_id": "col_1792212"
    },

    # -------------------------------------------------------------
    # 4. GRÄBERFELDER GLOBASNITZ & JAUNSTEIN
    # -------------------------------------------------------------
    {
        "id": "qa_graeberfeld_globasnitz_fakten",
        "lang": "de",
        "category": "Gräberfeld Globasnitz",
        "question": "Wie viele Gräber wurden im Gräberfeld von Globasnitz ausgegraben?",
        "variations": [
            "Wie groß ist der Friedhof von Globasnitz?",
            "Anzahl Gräber Globasnitz",
            "425 Gräber Globasnitz",
            "440 Bestattungen Globasnitz",
            "Größter Friedhof Österreichs Spätantike"
        ],
        "answer": "Das östlich des Ortskerns von Globasnitz gelegene Gräberfeld wurde zwischen 1999 und 2008 systematisch untersucht. Mit rund 425 Gräbern und etwa 440 Bestattungen ist es der größte spätantik-merowingerzeitliche Bestattungsplatz Österreichs und das einzige umfassend erforschte Gräberfeld einer Straßenstation in Noricum (Binder et al. 2016; Ladstätter 2000).",
        "citations": ["Binder et al. (2016)", "Ladstätter (2000)"],
        "keywords": ["gräberfeld", "globasnitz", "425", "440", "bestattungen", "michaela binder", "sabine ladstätter", "friedhof", "spätantike", "merowinger"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_kirchen_graeberfeld_globasnitz",
        "lang": "de",
        "category": "Gräberfeld Globasnitz",
        "question": "Gab es frühchristliche Kirchen im Gräberfeld von Globasnitz?",
        "variations": [
            "Kirche im Friedhof Globasnitz",
            "Frühchristliche Kirche Globasnitz Gräberfeld",
            "Zwei Kirchen Globasnitz Gräberfeld"
        ],
        "answer": "Ja, innerhalb des Friedhofsareals wurden die Fundamente zweier aufeinanderfolgender Kirchen freigelegt. Die ältere Kirche wurde bereits im letzten Drittel des 4. Jahrhunderts errichtet. Sie ist damit älter als die frühesten bisher bekannten Kirchenbauten auf dem Hemmaberg (Ladstätter 2000; Gugl et al.).",
        "citations": ["Ladstätter (2000)", "Christian Gugl et al."],
        "keywords": ["kirchen", "friedhof", "globasnitz", "4. jahrhundert", "frühchristlich", "ältere kirche", "hemmaberg"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_graeberfeld_globasnitz_kontaktregion",
        "lang": "de",
        "category": "Gräberfeld Globasnitz",
        "question": "Warum wird das Gräberfeld von Globasnitz als Zeugnis einer 'Kontaktregion' bezeichnet?",
        "variations": [
            "Kontaktregion Globasnitz",
            "Beigaben Gräberfeld Globasnitz",
            "Ostgoten Merowinger Globasnitz",
            "Fibeln Gürtel Globasnitz"
        ],
        "answer": "Rund 70 % der Gräber waren beigabenlos, doch die beigabenführenden Gräber (Ende 5. bis Mitte 6. Jh.) enthielten herausragende Trachtbestandteile wie Fibeln, Gürtelbeschläge und Perlen. Diese Ausstattungsstücke belegen weitreichende interregionale Netzwerke nach West-, Ost- und Südeuropa. Der Friedhof gilt daher als Musterbeispiel einer Kontaktregion, in der sich romanische, ostgotische, mediterrane und merowingische Einflüsse überlagerten (Ladstätter 2000; Binder et al. 2016).",
        "citations": ["Ladstätter (2000)", "Binder et al. (2016)"],
        "keywords": ["kontaktregion", "beigaben", "fibeln", "gürtel", "perlen", "ostgoten", "merowinger", "netzwerk", "binder", "ladstätter"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_graeberfeld_jaunstein",
        "lang": "de",
        "category": "Gräberfeld Jaunstein",
        "question": "Was zeichnet das frühmittelalterliche Gräberfeld von Jaunstein aus?",
        "variations": [
            "Gräberfeld Jaunstein",
            "Jaunstein Frühmittelalter",
            "Karantanisches Gräberfeld Jaunstein",
            "Köttlach-Kultur Jaunstein",
            "Schmuck Jaunstein"
        ],
        "answer": "Jaunstein ist ein bedeutendes frühmittelalterliches Reihengräberfeld der slawisch-karantanischen Epoche (Köttlach-Kultur, 8.–10. Jh.). Bei den Ausgrabungen wurden hunderte Gräber mit reichhaltigem Trachtschmuck (charakteristische Korbgehänge, Ohrringe, Ringe, Perlenketten) und Waffen geborgen. Die Funddaten sind in der Subcollection JAU auf ARCHE archiviert.",
        "citations": ["Hagmann & Reiner (2023)", "Hagmann & Reiner (2025)"],
        "keywords": ["jaunstein", "gräberfeld", "frühmittelalter", "karantanien", "slawisch", "köttlach", "korbgehänge", "jau"],
        "graph_node_id": "col_1792303"
    },

    # -------------------------------------------------------------
    # 5. IUENNA-PROJEKT, ARCHE, FAIR/CARE & DATEN
    # -------------------------------------------------------------
    {
        "id": "qa_projekt_akronym",
        "lang": "de",
        "category": "IUENNA-Projekt",
        "question": "Was bedeutet der Name des Projekts IUENNA?",
        "variations": [
            "Was heißt IUENNA?",
            "Wofür steht IUENNA?",
            "IUENNA Akronym Bedeutung",
            "Projektname IUENNA"
        ],
        "answer": "IUENNA ist ein wissenschaftliches Akronym für 'openIng the soUthErn jauNtal as a micro-regioN for future Archaeology'. Das durch das Go!Digital 3.0 Programm der Österreichischen Akademie der Wissenschaften (ÖAW) geförderte Projekt betrachtet Hemmaberg, Globasnitz, Jaunstein und St. Stefan erstmals ganzheitlich als zusammenhängende archäologische Mikroregion (Hagmann & Reiner 2023).",
        "citations": ["Hagmann & Reiner (2023)"],
        "keywords": ["akronym", "bedeutung", "godigital", "öaw", "mikroregion", "opening the southern jauntal", "hagmann", "waldhart"],
        "graph_node_id": "top_iuenna"
    },
    {
        "id": "qa_projekt_partner",
        "lang": "de",
        "category": "IUENNA-Projekt",
        "question": "Welche Institutionen waren am Projekt IUENNA beteiligt?",
        "variations": [
            "Wer leitet IUENNA?",
            "Partner IUENNA",
            "Beteiligte Institutionen IUENNA",
            "Wer hat bei IUENNA mitgearbeitet?"
        ],
        "answer": "IUENNA wurde gemeinsam von Dr. Dominik Hagmann (Landesmuseum für Kärnten / kärnten.museum) und Dipl.-Ing. Franziska Waldhart (ÖAI an der ÖAW) geleitet. Beteiligte Projektpartner sind das kärnten.museum, das Österreichische Archäologische Institut (ÖAI), das Austrian Centre for Digital Humanities and Cultural Heritage (ACDH-CH), das Bundesdenkmalamt (BDA) und die ARDIG – Archäologischer Dienst GesmbH (Hagmann & Reiner 2023).",
        "citations": ["Hagmann & Reiner (2023)"],
        "keywords": ["partner", "institutionen", "leitung", "hagmann", "waldhart", "kärnten.museum", "öai", "acdh-ch", "bda", "ardig"],
        "graph_node_id": "top_iuenna"
    },
    {
        "id": "qa_arche_sammlungsumfang",
        "lang": "de",
        "category": "ARCHE & Forschungsdaten",
        "question": "Wie groß ist die IUENNA-Sammlung im Repositorium ARCHE?",
        "variations": [
            "Wie viele Objekte hat IUENNA auf ARCHE?",
            "Umfang ARCHE Sammlung",
            "Speicherplatz IUENNA ARCHE",
            "Wie viele Dateien umfasst IUENNA?"
        ],
        "answer": "Die 2025 veröffentlichte IUENNA-Datensammlung im Repositorium ARCHE umfasst 20.788 digitale Objekte mit einem Gesamtvolumen von rund 356,68 GB. Sie ist in sechs semantische Untersammlungen gegliedert: HB (Hemmaberg), GLO (Globasnitz), JAU (Jaunstein), STE (St. Stefan), TAL (Jauntal regional) und RET (Retrodigitalisate; Hagmann & Reiner 2025).",
        "citations": ["Hagmann & Reiner (2025)", "Christian Gugl et al."],
        "keywords": ["arche", "umfang", "20788", "356 gb", "subcollections", "hb", "glo", "jau", "ste", "tal", "ret"],
        "graph_node_id": "top_iuenna"
    },
    {
        "id": "qa_fair_care_prinzipien",
        "lang": "de",
        "category": "ARCHE & Forschungsdaten",
        "question": "Welche Rolle spielen die FAIR- und CARE-Prinzipien bei IUENNA?",
        "variations": [
            "Was bedeuten FAIR und CARE bei IUENNA?",
            "Datenethik IUENNA",
            "Open Science FAIR CARE"
        ],
        "answer": "IUENNA setzt konsequent auf Open Science: Die Daten folgen den FAIR-Prinzipien (Findable, Accessible, Interoperable, Reusable) durch standardisierte Metadaten, offene Formate und permanente PIDs/DOIs. Darüber hinaus berücksichtigt das Projekt ausdrücklich die CARE-Prinzipien (Collective Benefit, Authority to Control, Responsibility, Ethics) für den ethisch verantwortungsvollen und gemeinwohlorientierten Umgang mit kulturellem Erbe (Christian Gugl et al.; Hagmann & Reiner 2023).",
        "citations": ["Christian Gugl et al.", "Hagmann & Reiner (2023)"],
        "keywords": ["fair", "care", "open science", "datenethik", "metadaten", "interoperabilität", "arche"],
        "graph_node_id": "top_iuenna"
    },
    {
        "id": "qa_qgis_download_gpkg",
        "lang": "de",
        "category": "GIS & Web-Mapping",
        "question": "Wie kann ich die Geodaten des Projekts direkt in QGIS nutzen?",
        "variations": [
            "Download QGIS Geodaten",
            "Wo finde ich das GeoPackage?",
            "IUENNA-WMA.gpkg herunterladen",
            "GIS Daten Jauntal"
        ],
        "answer": "Sie können das vollständige GIS-Paket als standardisiertes GeoPackage ('IUENNA-WMA.gpkg', ca. 7,8 MB) direkt aus dem GitHub-Repositorium oder über das Web-Mapping-Portal herunterladen. Es enthält alle erfassten Fundstellen, Grabungsgrenzen und Vektorschichten im WGS84-Koordinatensystem und kann ohne Konvertierung direkt per Drag-and-Drop in QGIS oder ArcGIS geladen werden.",
        "citations": ["Hagmann & Reiner (2023)"],
        "keywords": ["qgis", "geopackage", "gpkg", "download", "wma", "gis", "arcgis", "vektordaten", "wgs84"],
        "graph_node_id": "top_iuenna"
    },

    # -------------------------------------------------------------
    # 5. PERSONEN, FORSCHERINNEN & PROJEKTLEITUNG (Ladstätter, Binder, Profant, Srienc, Gugl, Hagmann, Winkler)
    # -------------------------------------------------------------
    {
        "id": "qa_person_sabine_ladstaetter",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer war Sabine Ladstätter und welche Bedeutung haben ihre Forschungen für den Hemmaberg?",
        "variations": [
            "Wer war Sabine Ladstätter?",
            "Wer ist Sabine Ladstätter?",
            "Sabine Ladstätter",
            "Forschungen Sabine Ladstätter Hemmaberg",
            "Ladstätter Hemmaberg Monographie",
            "Welche Rolle spielt Sabine Ladstätter?",
            "Was hat Sabine Ladstätter erforscht?"
        ],
        "answer": "Dr. Sabine Ladstätter (1968–2024) war eine herausragende österreichische Klassische Archäologin und langjährige Direktorin des Österreichischen Archäologischen Instituts (ÖAI) der ÖAW. Ihre grundlegenden Forschungen und Publikationen zu den Ausgrabungen auf dem Hemmaberg – insbesondere ihre umfassende Monografie zu den Kleinfunden und der Keramik ('Die materielle Kultur der spätantiken Höhensiedlung auf dem Hemmaberg', 2000) – schufen das chronologische und kulturhistorische Fundament für das Verständnis des spätantiken Pilgerzentrums. Ihre Arbeiten und retrodigitalisierten Dokumentationen sind ein Kernbestandteil der im IUENNA-Projekt aufbereiteten Forschungsgeschichte.",
        "citations": ["Ladstätter (2000)", "Ladstätter (2002)", "Hagmann & Reiner (2025)"],
        "keywords": ["sabine ladstätter", "ladstätter", "archäologin", "öai", "oeai", "hemmaberg", "kleinfunde", "materielle kultur", "keramik", "spätantike", "pilgerzentrum", "direktorin"],
        "graph_node_id": "col_1792825"
    },
    {
        "id": "qa_person_michaela_binder",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer ist Michaela Binder und welche Rolle spielt ihre bioarchäologische Forschung in IUENNA?",
        "variations": [
            "Wer ist Michaela Binder?",
            "Michaela Binder",
            "Bioarchäologie Michaela Binder",
            "Anthropologie Hemmaberg Binder",
            "Welche Rolle spielt Michaela Binder?",
            "Was hat Michaela Binder erforscht?"
        ],
        "answer": "Dr. Michaela Binder ist Bioarchäologin und Anthropologin am Österreichischen Archäologischen Institut (ÖAI) der ÖAW. Im Rahmen der Forschungen zum Hemmaberg und zu den Gräberfeldern des Jauntals leitete sie wegweisende bioarchäologische, paläopathologische und anthropologische Untersuchungen an den menschlichen Skelettresten. Ihre Arbeiten (u. a. Binder et al. 2016 zur europäischen Fußprothese des 6. Jhs.) untersuchen Lebensbedingungen, Krankheitsmuster, Mobilität und postmortale rituelle Praktiken der spätantiken Bevölkerung und bilden einen integrativen Schwerpunkt moderner digitaler Forschung im Projekt IUENNA.",
        "citations": ["Binder et al. (2016)", "Binder (2018)", "Hagmann & Reiner (2023)"],
        "keywords": ["michaela binder", "binder", "bioarchäologie", "anthropologie", "paläopathologie", "öai", "hemmaberg", "skelettreste", "kindersterblichkeit", "fußprothese", "jauntal"],
        "graph_node_id": "per_1756751"
    },
    {
        "id": "qa_person_elke_profant",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer ist Elke Profant und welche Bedeutung haben ihre numismatischen Arbeiten für IUENNA?",
        "variations": [
            "Wer ist Elke Profant?",
            "Elke Profant",
            "Numismatik Elke Profant",
            "Profant Münzschatz Globasnitz",
            "Was hat Elke Profant erforscht?"
        ],
        "answer": "Elke Profant ist Forscherin und Numismatikerin am Österreichischen Archäologischen Institut (ÖAI) der ÖAW, die maßgeblich an der Aufarbeitung und numismatischen Katalogisierung von Fundmünzen des Jauntals beteiligt ist. Gemeinsam mit Franziska Reiner publizierte sie die umfassende numismatische Neubearbeitung des 1946 geborgenen Hortfundes von 322 römischen Münzen aus Globasnitz ('Der spätantike Münzhort von Globasnitz / Iuenna', 2025). Ihre numismatischen Analysen sind ein wesentlicher Schlüssel zum Verständnis der spätantiken Geldwirtschaft und Chronologie des vicus.",
        "citations": ["Reiner & Profant (2025)", "Hagmann & Reiner (2023)"],
        "keywords": ["elke profant", "profant", "numismatik", "münzen", "hortfund", "322 münzen", "globasnitz", "reiner", "geldwirtschaft"],
        "graph_node_id": "per_1756742"
    },
    {
        "id": "qa_person_magdalena_srienc",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer ist Magdalena Srienc und welchen Beitrag leistet sie zur Archäologie des Jauntals?",
        "variations": [
            "Wer ist Magdalena Srienc?",
            "Magdalena Srienc",
            "Forschung Magdalena Srienc",
            "Srienc Archäologie Jauntal",
            "Magdalena Srienc-Sciesiek"
        ],
        "answer": "Magdalena T. Srienc-Ściesiek ist Archäologin und Forscherin am Österreichischen Archäologischen Institut (ÖAI) der ÖAW mit tiefem regionalem Bezug zum Jauntal / Podjuna und Kärnten. Ihre wissenschaftlichen Arbeiten und Grabungsdokumentationen tragen entscheidend zur Erschließung der archäologischen Landschaft, der Siedlungs- und Gräberfeldtopografie sowie zur regionalen Kulturvermittlung und Denkmalpflege bei. Im Kontext des Projekts IUENNA steht ihr Wirken beispielhaft für die präzise Dokumentation und Erhaltung des reichen kulturellen Erbes der Region.",
        "citations": ["Hagmann & Reiner (2025)", "Srienc et al. (2024)"],
        "keywords": ["magdalena srienc", "srienc", "srienc-ściesiek", "archäologin", "jauntal", "podjuna", "kärnten", "denkmalpflege", "kulturvermittlung", "siedlungstopografie", "öai"],
        "graph_node_id": "per_1756748"
    },
    {
        "id": "qa_person_hans_winkler",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer war Hans Winkler und warum sind seine Skizzen für IUENNA wichtig?",
        "variations": [
            "Wer war Hans Winkler?",
            "Hans Winkler",
            "Winkler Skizzen",
            "Hans Winkler St. Stefan",
            "Historische Skizzen Hans Winkler",
            "Welche Rolle spielten die Skizzen von Hans Winkler?"
        ],
        "answer": "Hans Winkler war ein historischer Forscher und Zeichner, der in den 1920er und 1930er Jahren detaillierte Skizzen und Fundmeldungen im Jauntal anfertigte. Seine retrodigitalisierten Skizzenbücher (in ARCHE in der Subcollection RET erfasst) lieferten der modernen Bauforschung (Christian Gugl et al.) entscheidende Hinweise zur Rekonstruktion und Neuinterpretation der rund zwei Hektar großen römischen Großvilla von St. Stefan.",
        "citations": ["Christian Gugl et al.", "Hagmann & Reiner (2023)"],
        "keywords": ["hans winkler", "winkler", "skizzen", "ret", "st. stefan", "villa", "retrodigitalisierung"],
        "graph_node_id": "col_1792572"
    },
    {
        "id": "qa_person_christian_gugl",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer ist Christian Gugl und welche Thesen vertritt er zu Iuenna?",
        "variations": [
            "Wer ist Christian Gugl?",
            "Christian Gugl",
            "Gugl Iuenna",
            "Gugl Tscherberg",
            "Was erforscht Christian Gugl?"
        ],
        "answer": "Priv.-Doz. Dr. Christian Gugl ist leitender Wissenschaftler am Österreichischen Archäologischen Institut (ÖAI / ÖAW) und Experte für römische Provinzialarchäologie und Siedlungstopografie. Er leitet die jüngste archäologische Neubewertung der Mikroregion Globasnitz. Gugl begründete die These, dass Globasnitz ein 7–9 ha großer vicus war, während die Straßenstation Iuenna der Tabula Peutingeriana beim Tscherberg lag, und analysierte die Großvilla St. Stefan.",
        "citations": ["Christian Gugl et al. (2024)"],
        "keywords": ["christian gugl", "gugl", "öai", "öaw", "tscherberg", "vicus", "st. stefan", "neubewertung"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_person_dominik_hagmann",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wer ist Dominik Hagmann und was ist seine Rolle im IUENNA-Projekt?",
        "variations": [
            "Wer ist Dominik Hagmann?",
            "Dominik Hagmann",
            "Projektleiter IUENNA",
            "Wer leitet das Projekt IUENNA?",
            "Hagmann IUENNA"
        ],
        "answer": "Dr. Dominik Hagmann ist Archäologe und Digital-Humanities-Spezialist am Österreichischen Archäologischen Institut (ÖAI / ÖAW) und Gesamtleiter des Projekts IUENNA ('Von der analogen Grabungsdokumentation zur FAIRen Forschungsdateninfrastruktur'). Gemeinsam mit Franziska Reiner (geb. Waldhart) und Nicola Math leitete und konzipierte er die digitale Rettung und Erschließung der über 20.000 analogen Grabungsdokumente aus dem Jauntal nach den FAIR- und CARE-Prinzipien für das Repositorium ARCHE.",
        "citations": ["Hagmann & Reiner (2023)", "Hagmann & Waldhart (2023)"],
        "keywords": ["dominik hagmann", "hagmann", "projektleiter", "öai", "öaw", "fair", "retrodigitalisierung", "arche"],
        "graph_node_id": "top_iuenna"
    },

    # -------------------------------------------------------------
    # 6. VERTIEFENDE ASPEKTE: BIOARCHÄOLOGIE, ALLTAG, MÜNZEN & METHODEN
    # -------------------------------------------------------------
    {
        "id": "qa_bioarch_fuss_prothese",
        "lang": "de",
        "category": "Bioarchäologie & Anthropologie",
        "question": "Was ist über die frühmittelalterliche Fußprothese vom Hemmaberg bekannt?",
        "variations": [
            "Fußprothese Hemmaberg",
            "Älteste Prothese Europas Hemmaberg",
            "Prothese 6. Jahrhundert Hemmaberg",
            "Grab Fußprothese Hemmaberg",
            "Wer trug die Prothese am Hemmaberg?",
            "Amputation Hemmaberg"
        ],
        "answer": "2013 wurde im Gräberfeld auf dem Gipfelplateau des Hemmabergs (6. Jh. n. Chr.) das Skelett eines erwachsenen Mannes mit einer Fußprothese entdeckt (Binder et al. 2016). Dem Individuum war der linke Fuß im Knöchelbereich amputiert worden; die Wunde verheilte vollständig. Anstelle des Fußes trug er eine kunstvolle Konstruktion aus einem Holzstumpf mit Eisenring, die ihm das Gehen ermöglichte, was durch sekundäre Arthrosen an Knien und Schultergürtel bestätigt wird. Es handelt sich um eine der ältesten nachgewiesenen Prothesen des Frühmittelalters in Europa und ein herausragendes Zeugnis spätantiker medizinischer Versorgung und sozialer Fürsorge.",
        "citations": ["Binder et al. (2016)", "Binder (2018)", "Ladstätter (2000)"],
        "keywords": ["fußprothese", "prothese", "amputation", "eisenring", "holzstumpf", "binder", "hemmaberg", "bioarchäologie", "6. jahrhundert", "arthrose", "medizin"],
        "graph_node_id": "col_1792415"
    },
    {
        "id": "qa_bioarch_schaedel_deformation",
        "lang": "de",
        "category": "Bioarchäologie & Anthropologie",
        "question": "Wurden im Gräberfeld von Globasnitz künstliche Schädeldeformationen nachgewiesen?",
        "variations": [
            "Künstliche Schädeldeformation Globasnitz",
            "Turmschädel Globasnitz",
            "Schädelverformung Ostgoten Globasnitz",
            "Schädeldeformationen Ostgotenzeit",
            "Bandagieren Säuglinge Schädel Globasnitz"
        ],
        "answer": "Ja, im ostgotenzeitlichen Gräberfeld von Globasnitz (5./6. Jh. n. Chr.) wurden bei mindestens 10 Individuen künstliche Schädeldeformationen (sogenannte Turmschädel) nachgewiesen (Binder et al. 2016; Ladstätter 2000). Diese wurden im Säuglingsalter durch straffes Bandagieren mit Tüchern und Brettchen erzielt. Die Praxis war ein elitäres Status- und Identitätsmerkmal unter ostgermanischem bzw. nomadischem Einfluss (Ostgoten, Alanen, Hunnen) und belegt die enge Einbindung der Siedlungsgemeinschaft in die völkerwanderungszeitliche Elitenkultur.",
        "citations": ["Binder et al. (2016)", "Ladstätter (2000)"],
        "keywords": ["schädeldeformation", "turmschädel", "schädelverformung", "bandagieren", "globasnitz", "ostgoten", "binder", "ladstätter", "völkerwanderungszeit", "status"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_bioarch_demografie",
        "lang": "de",
        "category": "Bioarchäologie & Anthropologie",
        "question": "Welche demografischen Unterschiede zeigen die Bestattungen in Globasnitz und auf dem Hemmaberg?",
        "variations": [
            "Demografie Gräberfelder Globasnitz Hemmaberg",
            "Anthropologie Globasnitz Hemmaberg",
            "Kindersterblichkeit Hemmaberg",
            "Geschlechterverteilung Gräberfeld Globasnitz",
            "aDNA Studie Globasnitz Hemmaberg"
        ],
        "answer": "Das Gräberfeld von Globasnitz (422 dokumentierte Gräber) weist eine bemerkenswert ausgewogene Demografie auf: 122 Männer, 119 Frauen und 102 Kinder/Jugendliche, was einer normalen sesshaften Dorfgemeinschaft entspricht (Binder et al. 2016; Ladstätter 2000). Auf dem Gipfelplateau des Hemmabergs hingegen ist der Anteil an Kindergräbern bei den intramuralen und ad sanctos-Bestattungen überproportional hoch (z.B. 21 Kinder/Jugendliche bei nur 7 Erwachsenen in einem Grabungsbereich), was den Wunsch nach sakralem Schutz im Heiltum widerspiegelt. Eine umfassende aDNA-Studie an rund 160 Individuen soll zudem Verwandtschaftsverhältnisse und Herkunftsmuster klären.",
        "citations": ["Ladstätter (2000)", "Binder et al. (2016)"],
        "keywords": ["demografie", "männer", "frauen", "kinder", "kindersterblichkeit", "ad sanctos", "adna", "hemmaberg", "globasnitz", "binder", "ladstätter", "anthropologie"],
        "graph_node_id": "col_1792415"
    },
    {
        "id": "qa_hemmaberg_alltag_wirtschaft",
        "lang": "de",
        "category": "Hemmaberg",
        "question": "Was verraten die archäologischen Funde über Alltag, Ernährung und Wirtschaft auf dem Hemmaberg?",
        "variations": [
            "Alltag und Wirtschaft Hemmaberg",
            "Ernährung auf dem Hemmaberg",
            "Keramik Hemmaberg 24848",
            "Abfallgrube 5. Jahrhundert Hemmaberg",
            "Was aßen die Menschen auf dem Hemmaberg?",
            "Weinamphoren Hemmaberg"
        ],
        "answer": "Ausgrabungen auf dem Hemmaberg erbrachten 24.848 dokumentierte Keramikfragmente, die eine Besiedlung von der Bronzezeit über das römische Iuppiter-Heiligtum bis in die Spätantike belegen. Eine um 450 n. Chr. verfüllte Abfallgrube lieferte exakte Einblicke in Alltag und Speisezettel: Die pflanzlichen Reste bestanden zu 96,3 % aus Getreide (Dinkel, Roggen, Gerste), ergänzt durch Ackerbohnen und Linsen. Bei den Tierknochen dominierte Rindfleisch vor Schwein und Schaf/Ziege. Mediterrane Feinkeramik (African Red Slip Ware) und Weinamphoren aus der Ägäis und dem östlichen Mittelmeer beweisen, dass die Höhensiedlung trotz Krisenzeiten über blühende Fernhandelsnetzwerke versorgt wurde (Forstenpointner et al. 2003; Ladstätter 2000).",
        "citations": ["Forstenpointner et al. (2003)", "Ladstätter (2000)", "Hagmann & Reiner (2023)"],
        "keywords": ["alltag", "wirtschaft", "ernährung", "keramik", "24848", "abfallgrube", "getreide", "dinkel", "roggen", "rindfleisch", "afrikanische sigillata", "amphoren", "forstenpointner"],
        "graph_node_id": "col_1792415"
    },
    {
        "id": "qa_globasnitz_muenzschatz",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Was ist über den Münzschatzfund von Globasnitz bekannt?",
        "variations": [
            "Münzschatz Globasnitz",
            "Römischer Münzschatz Globasnitz",
            "322 Münzen Globasnitz",
            "Münzhort Globasnitz 1946"
        ],
        "answer": "1946 wurde im Ortszentrum von Globasnitz (im Bereich des römischen vicus) ein Hortfund von 322 römischen Münzen geborgen (Reiner & Profant 2025). Der Fundkomplex besteht überwiegend aus Bronzemünzen des 3. und 4. Jahrhunderts n. Chr. und belegt sowohl die florierende Geldwirtschaft an der Kreuzung lokaler Verkehrswege als auch Krisen und Verbergungshorizonte in der Spätantike.",
        "citations": ["Reiner & Profant (2025)", "Piccottini (1978)"],
        "keywords": ["münzschatz", "hortfund", "322 münzen", "globasnitz", "vicus", "spätantike", "reiner", "profant"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_geophysik_methodik_reiner",
        "lang": "de",
        "category": "Topografische Neubewertung",
        "question": "Welche geophysikalischen Prospektionsmethoden wurden in Globasnitz und St. Stefan eingesetzt?",
        "variations": [
            "Geophysik Methodik Globasnitz",
            "Gradiometer und Georadar Globasnitz",
            "Reiner Profant 2025 Prospektion",
            "Wie wurde die Siedlung Globasnitz erforscht?",
            "Geräte Geophysik IUENNA"
        ],
        "answer": "In den Kampagnen 2020–2023 wurden modernste zerstörungsfreie Methoden kombiniert (Reiner & Profant 2025; Schwaiger & Reiner 2022): Ein motorisiertes 5-Kanal-Fluxgate-Gradiometer (0,5 m Sondenabstand) erfasste 21 Hektar geomagnetisch. Hochauflösendes Bodenradar (Georadar / GPR, 400 MHz) durchleuchtete rund 4 Hektar bis in 2 Meter Tiefe. Alle Messungen wurden per RTK-GPS (Leica GS18 T) zentimetergenau georeferenziert. Die Datenverarbeitung in ReflexW und ArcGIS Pro ermöglichte die exakte Rekonstruktion der 3 m breiten Nord-Süd-Straße im vicus und der Villenflügel von St. Stefan.",
        "citations": ["Reiner & Profant (2025)", "Schwaiger & Reiner (2022)"],
        "keywords": ["geophysik", "fluxgate", "gradiometer", "400 mhz", "georadar", "gpr", "rtk-gps", "reiner", "profant", "schwaiger", "arcgis", "prospektion"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_iuenna_datenumfang_nachhaltigkeit",
        "lang": "de",
        "category": "IUENNA-Projekt",
        "question": "Welchen Datenumfang hat das Projekt IUENNA und wie ist die Zugänglichkeit geregelt?",
        "variations": [
            "Datenumfang IUENNA",
            "Open Data IUENNA",
            "Lizenzen IUENNA ARCHE",
            "Wie viele Daten hat IUENNA?",
            "Simonsberg Hangrutsch Daten",
            "Digitale Nachhaltigkeit IUENNA"
        ],
        "answer": "Das Go!Digital-3.0-Projekt (2023–2024, Leitung: D. Hagmann & F. Reiner mit N. Math) bündelt über ein Jahrhundert Forschung zu mehr als 200 Fundstellen. Die archivierte Sammlung in ARCHE umfasst über 20.000 digitale Objekte und mehr als 350 GB (aus 200 GB analogen Rohdaten wurden 650 GB hochauflösende Scans und Geodaten). Der Zugang ist gestuft geregelt: Rund 20 % der Datensätze sind als Open Access (CC BY 4.0) frei downloadbar, 100 % der Metadaten stehen unter CC0, sensible Fundortdaten werden zum Schutz der Bodendenkmale auf Anfrage bereitgestellt. Die Dringlichkeit der digitalen Rettung zeigte der Hangrutsch am Simonsberg nach Extremwetter am 6. August 2023.",
        "citations": ["Hagmann & Reiner (2025)", "Hagmann et al. (2024)"],
        "keywords": ["datenumfang", "350 gb", "650 gb", "200 fundstellen", "20000 objekte", "open access", "cc by 4.0", "cc0", "simonsberg", "hangrutsch", "daten-upcycling", "nachhaltigkeit"],
        "graph_node_id": "top_iuenna"
    },
    {
        "id": "qa_forschungsgeschichte_ueberblick",
        "lang": "de",
        "category": "Forschungsgeschichte & Personen",
        "question": "Wie verlief die Forschungsgeschichte im Jauntal von den Anfängen bis heute?",
        "variations": [
            "Forschungsgeschichte Jauntal",
            "Wer hat wann im Jauntal geforscht?",
            "Geschichte der Ausgrabungen Hemmaberg Globasnitz",
            "Pioniere der Archäologie Jauntal"
        ],
        "answer": "Die Dokumentation begann im späten 15. Jahrhundert, als reisende Mönche eine römische Inschrift aufzeichneten. 1838 fasste M. F. von Jabornegg-Altenfels erste Funde zu Iuenna zusammen; 1887 beschrieb Baron Karl Hauser antikes Mauerwerk auf dem Hemmaberg. Die systematische Feldforschung leitete 1906 Notar Hans Winkler ein, gefolgt von Rudolf Eggers Grabungen 1914. Bedeutende Pionierarbeiten leisteten Forscherinnen wie Sabine Ladstätter mit ihren grundlegenden Analysen zur materiellen Kultur und den Kleinfunden des Hemmabergs sowie Michaela Binder mit modernen bioarchäologischen Untersuchungen an den Gräberfeldern. Seit 2020 verbinden großflächige Geophysik-Kampagnen und das Go!Digital-Projekt IUENNA (2023–2024) historische Dokumente mit modernster digitaler Prospektion.",
        "citations": ["Ladstätter (2000)", "Binder et al. (2016)", "Hagmann & Reiner (2025)"],
        "keywords": ["forschungsgeschichte", "mönche", "jabornegg-altenfels", "hauser", "winkler", "egger", "ladstätter", "binder", "ausgrabungen", "chronologie"],
        "graph_node_id": "top_iuenna"
    },
    # -------------------------------------------------------------
    # 7. ENGLISCHE KERNFRAGEN (Trilingual Support)
    # -------------------------------------------------------------
    {
        "id": "qa_en_tscherberg_reassessment",
        "lang": "en",
        "category": "Topographical Reassessment",
        "question": "Was Globasnitz really the Roman road station Iuenna?",
        "variations": [
            "Where was the Roman road station Iuenna located?",
            "Is Globasnitz identical to Iuenna?",
            "Why is the identification of Globasnitz as Iuenna challenged?",
            "Tscherberg and Iuenna"
        ],
        "answer": "Recent comprehensive archaeological syntheses (Christian Gugl et al.) challenge the traditional equation. Globasnitz was a non-urban vicus of 7–9 hectares, but it lay more than 3 kilometres south of the main Celeia–Virunum highway. The road station Iuenna is now tentatively located at Tscherberg, which lay directly on the Roman main road and aligns with the distance of 23 Roman miles recorded on the Tabula Peutingeriana.",
        "citations": ["Christian Gugl et al.", "Ladstätter (2000)"],
        "keywords": ["globasnitz", "iuenna", "tscherberg", "road station", "mansio", "vicus", "celeia", "virunum", "tabula peutingeriana"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_en_st_stefan_villa",
        "lang": "en",
        "category": "Villa St. Stefan",
        "question": "What is known about the Roman villa complex at St. Stefan?",
        "variations": [
            "Roman villa St. Stefan",
            "Super-villa St. Stefan",
            "Where is the villa of St. Stefan?",
            "Bath building St. Stefan"
        ],
        "answer": "The Roman villa complex at St. Stefan lies about 1.2 km north of Globasnitz and covered around 2 hectares with at least three building phases. It represents an orthogonally planned estate typical of southern Noricum with functional separation of residential and farming quarters, courtyard walls, a grand room with two opposing apses, and a dedicated bath building with hypocausts (Christian Gugl et al.; Schwaiger & Reiner 2022).",
        "citations": ["Christian Gugl et al.", "Schwaiger & Reiner (2022)"],
        "keywords": ["st. stefan", "villa", "estate", "orthogonal", "bath", "hypocaust", "gugl"],
        "graph_node_id": "col_1792411"
    },

    {
        "id": "qa_en_bioarch_foot_prosthesis",
        "lang": "en",
        "category": "Bioarchaeology",
        "question": "What is known about the early medieval foot prosthesis from Hemmaberg?",
        "variations": [
            "Foot prosthesis Hemmaberg",
            "Oldest prosthesis in Europe Hemmaberg",
            "6th century prosthesis Hemmaberg",
            "Amputation Hemmaberg"
        ],
        "answer": "In 2013, the grave of an adult male from the 6th century AD was discovered in the Hemmaberg summit cemetery (Binder et al. 2016). The individual had undergone a completely healed amputation of the left foot at ankle level. He wore an elaborate prosthesis consisting of a wooden peg with an iron ring and leather/organic fastenings, allowing functional mobility confirmed by secondary arthrosis in knee and shoulder. It represents one of the earliest securely contextualised functional prostheses from early medieval Europe.",
        "citations": ["Binder et al. (2016)", "Binder (2018)"],
        "keywords": ["prosthesis", "foot prosthesis", "amputation", "iron ring", "wooden peg", "hemmaberg", "binder", "6th century"],
        "graph_node_id": "col_1792415"
    },
    {
        "id": "qa_en_bioarch_cranial_deformation",
        "lang": "en",
        "category": "Bioarchaeology",
        "question": "Were artificial cranial deformations discovered in the Globasnitz cemetery?",
        "variations": [
            "Artificial cranial deformation Globasnitz",
            "Elongated skulls Globasnitz",
            "Head binding Ostrogoths Globasnitz",
            "Tower skulls Globasnitz"
        ],
        "answer": "Yes, at least 10 individuals with intentional artificial cranial deformations were identified in the Ostrogothic-period cemetery of Globasnitz (Binder et al. 2016; Ladstätter 2000). The elongation was achieved during infancy through tight bandage wrapping. This custom was an elite marker influenced by eastern Germanic and Eurasian nomad populations (Ostrogoths, Alans, Huns) during the Migration Period in 5th- and 6th-century Noricum.",
        "citations": ["Binder et al. (2016)", "Ladstätter (2000)"],
        "keywords": ["cranial deformation", "head binding", "globasnitz", "ostrogoths", "migration period", "binder", "ladstätter", "artificial elongation"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_en_data_volume_sustainability",
        "lang": "en",
        "category": "IUENNA Project",
        "question": "What is the data volume and digital preservation policy of the IUENNA project?",
        "variations": [
            "Data volume IUENNA",
            "Open Access IUENNA ARCHE",
            "Simonsberg landslide data preservation",
            "How many files in IUENNA?"
        ],
        "answer": "Funded by the Austrian Academy of Sciences (Go!Digital 3.0, 2023–2024; D. Hagmann & F. Reiner with N. Math), IUENNA collated research from over 200 sites. The authoritative IUENNA primary-resource corpus contains 20,355 archived files, while the validated knowledge graph contains 21,071 nodes (21,061 ARCHE-backed entities); the archived holdings comprise over 356 GB (scaling from 200 GB raw documentation to 650 GB high-resolution assets). Access is tiered: approx. 20% is open access under CC BY 4.0, 100% of metadata is CC0, while sensitive archaeological spatial data is restricted upon request to protect monuments. The urgency of digital preservation was highlighted by the Simonsberg landslide on 6 August 2023.",
        "citations": ["Hagmann & Reiner (2025)", "Hagmann et al. (2024)"],
        "keywords": ["data volume", "arche", "356 gb", "open access", "cc by 4.0", "cc0", "simonsberg", "landslide", "sustainability", "fair"],
        "graph_node_id": "top_iuenna"
    },
    # -------------------------------------------------------------
    # 8. SLOWENISCHE KERNFRAGEN (Podjuna / Koroška)
    # -------------------------------------------------------------
    {
        "id": "qa_sl_iuenna_tscherberg",
        "lang": "sl",
        "category": "Topografska presoja",
        "question": "Ali je bil Globasnitz res rimska cestna postaja Iuenna?",
        "variations": [
            "Kje je ležala rimska cestna postaja Iuenna?",
            "Ali je Globasnitz Iuenna?",
            "Zakaj je lokacija Iuenne v Globasnici sporna?",
            "Tscherberg Iuenna"
        ],
        "answer": "Novejše arheološke raziskave (Christian Gugl et al.) to tradicionalno enačitev postavljajo pod vprašaj. Globasnitz je bil neurbani vicus velikosti 7–9 hektarov, vendar je ležal več kot 3 kilometre južno od glavne rimske ceste Celeia–Virunum. Kot verjetnejša lokacija cestne postaje Iuenna se danes predlaga Tscherberg, ki je ležal neposredno ob glavni trasi in ustreza razdalji 23 rimskih milj na Tabuli Peutingeriani.",
        "citations": ["Christian Gugl et al.", "Ladstätter (2000)"],
        "keywords": ["globasnitz", "globasnica", "iuenna", "tscherberg", "cestna postaja", "vicus", "podjuna", "tabula peutingeriana"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_sl_st_stefan_steben",
        "lang": "sl",
        "category": "Rimska vila Šteben",
        "question": "Kaj je znano o kompleksu rimske vile v Štebnu (St. Stefan)?",
        "variations": [
            "Rimska vila Šteben",
            "Kompleks vile v Štebnu",
            "Kje leži Šteben?",
            "Kopališče Šteben"
        ],
        "answer": "V Štebnu, približno 1,2 km severno od Globasnitza, leži približno 2 hektara velik večfazni kompleks rimske vile z najmanj tremi gradbenimi fazami. Obsegal je dvoriščne zidove, dvorano z dvema nasproti ležečima apsidama ter kopališko stavbo s hipokavstom in vodnim kanalom (Christian Gugl et al.; Schwaiger & Reiner 2022).",
        "citations": ["Christian Gugl et al.", "Schwaiger & Reiner (2022)"],
        "keywords": ["šteben", "st. stefan", "rimska vila", "kopališče", "hipokavst", "apside", "podjuna"],
        "graph_node_id": "col_1792411"
    },
    {
        "id": "qa_sl_bioarheologija_proteza",
        "lang": "sl",
        "category": "Bioarheologija",
        "question": "Kaj je znano o zgodnjesrednjeveški nožni protezi s Hemmaberga?",
        "variations": [
            "Nožna proteza Hemmaberg",
            "Najstarejša proteza v Evropi Hemmaberg",
            "Amputacija Hemmaberg",
            "Proteza 6. stoletje Hemmaberg"
        ],
        "answer": "Leta 2013 je bil na vršnem platoju Hemmaberga (grob iz 6. stoletja n. št.) odkrit moški z zaceljeno amputacijo levega stopala v gležnju (Binder et al. 2016). Namesto stopala je nosil protezo iz lesenega čepa in železnega obroča. Rentgen, CT in artroza na kolenih ter ramenih potrjujejo funkcionalno rabo proteze (morda ob opori). Gre za enega najstarejših evropskih primerov proteze neposredno ob uporabniku in izjemen dokaz medicinske nege ter socialne podpore v pozni antiki.",
        "citations": ["Binder et al. (2016)", "Binder (2018)"],
        "keywords": ["nožna proteza", "proteza", "amputacija", "hemmaberg", "železni obroč", "binder", "6. stoletje", "bioarheologija"],
        "graph_node_id": "col_1792415"
    },
    {
        "id": "qa_sl_bioarheologija_lobanje",
        "lang": "sl",
        "category": "Bioarheologija",
        "question": "Ali so bile na grobišču v Globasnici odkrite umetne deformacije lobanj?",
        "variations": [
            "Umetne deformacije lobanj Globasnica",
            "Deformirane lobanje Globasnitz",
            "Povijanje glav vzhodni goti Globasnica"
        ],
        "answer": "Da, na grobišču iz časa Vzhodnih Gotov v Globasnici (5. in 6. stoletje n. št.) so bile pri najmanj 10 posameznikih ugotovljene kranijske deformacije (umetno podaljšane lobanje; Binder et al. 2016; Ladstätter 2000). Deformacijo so dosegli v zgodnjem otroštvu s tesnim povijanjem z obvezami. Šlo je za elitni znak identitete in družbenega statusa pod vplivom vzhodnogermanskih in nomadskih skupin (Vzhodni Goti, Alani, Huni).",
        "citations": ["Binder et al. (2016)", "Ladstätter (2000)"],
        "keywords": ["deformacije lobanj", "umetna deformacija", "globasnica", "globasnitz", "vzhodni goti", "grobišče", "binder", "ladstätter"],
        "graph_node_id": "col_1792169"
    },
    {
        "id": "qa_sl_obseg_podatkov_iuenna",
        "lang": "sl",
        "category": "Projekt IUENNA",
        "question": "Kakšen je obseg podatkov in digitalna trajnost projekta IUENNA?",
        "variations": [
            "Obseg podatkov IUENNA",
            "Odprti podatki IUENNA ARCHE",
            "Zemeljski plaz Simonsberg",
            "Koliko podatkov ima IUENNA?"
        ],
        "answer": "Projekt IUENNA (Go!Digital 3.0, 2023–2024, vodji: D. Hagmann in F. Reiner z N. Math) združuje več kot stoletje raziskav na več kot 200 najdiščih. Zbirka v repozitoriju ARCHE obsega več kot 20.000 digitalnih objektov in več kot 356 GB podatkov (skupaj 650 GB skenov in digitaliziranih gradiv). Dostop je stopenjski: ca. 20 % je prosto dostopnih (CC BY 4.0), 100 % metapodatkov je CC0, občutljive lokacijske točke pa so na voljo na zahtevo za zaščito dediščine. Pomen digitalnega ohranjanja je poudaril tudi plaz na Simonsbergu 6. avgusta 2023.",
        "citations": ["Hagmann & Reiner (2025)", "Hagmann et al. (2024)"],
        "keywords": ["obseg podatkov", "arche", "356 gb", "cc by 4.0", "cc0", "simonsberg", "plaz", "trajnost", "fair", "podjuna"],
        "graph_node_id": "top_iuenna"
    }

]

def generate_fine_tune_datasets():
    print(f"[*] Generating synthetic Q&A corpus ({len(SYNTHETIC_CORPUS)} items)...")

    # 1. Output data/iuenna_synthetic_qa.json
    with open(QA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(SYNTHETIC_CORPUS, f, ensure_ascii=False, indent=2)
    print(f"[+] Written synthetic Q&A database to {QA_OUTPUT_FILE}")

    # 2. Output Alpaca Instruction Dataset
    alpaca_data = []
    for qa in SYNTHETIC_CORPUS:
        # Add primary question
        alpaca_data.append({
            "instruction": "Beantworte die folgende Frage zum archäologischen Projekt IUENNA und der Mikroregion Jauntal präzise und wissenschaftlich fundiert.",
            "input": qa["question"],
            "output": qa["answer"]
        })
        # Add variations
        for v in qa.get("variations", []):
            alpaca_data.append({
                "instruction": "Beantworte die folgende Frage zum archäologischen Projekt IUENNA und der Mikroregion Jauntal präzise und wissenschaftlich fundiert.",
                "input": v,
                "output": qa["answer"]
            })

    with open(ALPACA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(alpaca_data, f, ensure_ascii=False, indent=2)
    print(f"[+] Written Alpaca fine-tuning dataset to {ALPACA_OUTPUT_FILE} ({len(alpaca_data)} training pairs)")

    # 3. Output ShareGPT / ChatML format
    sharegpt_data = []
    for item in alpaca_data:
        sharegpt_data.append({
            "conversations": [
                {"from": "system", "value": "Du bist der wissenschaftliche Assistent für das archäologische Forschungsprojekt IUENNA (ÖAW / ÖAI / kärnten.museum)."},
                {"from": "human", "value": item["input"]},
                {"from": "gpt", "value": item["output"]}
            ]
        })

    with open(SHAREGPT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(sharegpt_data, f, ensure_ascii=False, indent=2)
    print(f"[+] Written ShareGPT dataset to {SHAREGPT_OUTPUT_FILE}")

    # 4. Output JSONL for Hugging Face / Unsloth training
    with open(JSONL_OUTPUT_FILE, "w", encoding="utf-8") as f:
        for entry in sharegpt_data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[+] Written ChatML JSONL dataset to {JSONL_OUTPUT_FILE}")

if __name__ == "__main__":
    generate_fine_tune_datasets()
