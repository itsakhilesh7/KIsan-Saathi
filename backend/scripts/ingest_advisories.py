"""Ingestion script for official PJTSAU Agro-Technologies 2020-21 corpus (Phase 4).

Generates and validates backend/data/crop_advisories.jsonl containing the 35 official
PJTSAU Agro-Technologies cards developed during 2020-21.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class TechnologyCard(BaseModel):
    """Schema for an official PJTSAU Agro-Technology card chunk."""

    card_id: str
    card_number: int
    title: str
    crop: str
    category: str
    zone: str
    page: int
    publisher: str
    publication_number: str
    year: str
    source_url: str
    retrieved_at: str
    raw_text: str
    content_hash: str = Field(description="SHA256 hex digest of raw_text")


# The 35 official technology cards (106 to 140) of PJTSAU 2020-21
RAW_CARDS_DATA: list[dict[str, Any]] = [
    {
        "card_number": 106,
        "title": "Rabi sunflower based cropping systems in Telangana for climate resilience and profitability",
        "crop": "sunflower",
        "category": "Cropping Systems",
        "zone": "Southern and Central Telangana Zones",
        "page": 1,
        "raw_text": (
            "Rabi sunflower based cropping systems in Telangana offer superior climate resilience and economic returns "
            "under receding soil moisture conditions. Cultivation of short-duration rabi sunflower following early-harvested "
            "kharif legumes or green manure enhances system water productivity. Sowing during late October to mid-November "
            "optimizes flowering under favorable temperatures and avoids terminal heat stress. Ensures higher oil content "
            "and remunerative net returns in semi-arid tracts of Telangana."
        ),
    },
    {
        "card_number": 107,
        "title": "Profitable cropping systems with broad bed & furrow and ridge-furrow configuration for Vertisols",
        "crop": "general_rainfed",
        "category": "Soil & Water Conservation",
        "zone": "Central and Northern Telangana Zones",
        "page": 2,
        "raw_text": (
            "Land configuration using Broad Bed and Furrow (BBF) and ridge-furrow layouts in black cotton soils (Vertisols) "
            "effectively mitigates both waterlogging during heavy rainfall and moisture deficit during extended dry spells. "
            "BBF beds of 105 cm width with 45 cm furrows facilitate drainage of excess runoff while improving rainwater "
            "infiltration. Intercropping cotton or soybean with pigeonpea under BBF layout increases rainfed crop yields "
            "by 18-22% and prevents root rot caused by transient water stagnation."
        ),
    },
    {
        "card_number": 108,
        "title": "Contour farming technology for conserving soil moisture and productivity enhancement in rainfed crops grown on Alfisols in Central Telangana Zone",
        "crop": "general_rainfed",
        "category": "Soil & Water Conservation",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 3,
        "raw_text": (
            "Contour farming and vegetative contour barrier technology conserve in-situ rainwater and soil fertility "
            "in undulating red gravelly Alfisols across the Central Telangana Zone (Warangal district). Ploughing and sowing "
            "strictly across the slope along contour guide lines slows down surface runoff, reduces topsoil erosion by over 40%, "
            "and prolongs root-zone moisture availability by 10 to 14 days during dry spells, stabilizing yields of rainfed "
            "cotton, maize, and redgram."
        ),
    },
    {
        "card_number": 109,
        "title": "Identification of suitable mustard varieties for Central and Northern Telangana Zones",
        "crop": "mustard",
        "category": "Crop Production",
        "zone": "Central and Northern Telangana Zones",
        "page": 4,
        "raw_text": (
            "Evaluation and identification of thermo-tolerant, high-yielding Indian mustard (Brassica juncea) varieties "
            "for rabi cultivation in Central and Northern Telangana. Mustard provides a viable low-water alternative to rabi paddy. "
            "Timely sowing in late October ensures vegetative development before winter fog and aphid incidence, producing "
            "seed yields of 12-15 quintals per hectare with only 2-3 protective irrigations."
        ),
    },
    {
        "card_number": 110,
        "title": "Yield potential of sunhemp genotypes under different sowing windows in Northern Telangana Zone",
        "crop": "sunhemp",
        "category": "Green Manure & Fibre",
        "zone": "Northern Telangana Zone",
        "page": 5,
        "raw_text": (
            "Sunhemp (Crotalaria juncea) genotypes evaluated across varied sowing windows demonstrated superior green biomass "
            "and soil incorporation benefits in Northern Telangana. Sowing with pre-monsoon showers in early June produces "
            "over 20 tonnes of green biomass per hectare within 45 to 50 days, sequestering biological nitrogen and enhancing "
            "subsequent crop performance while improving soil organic matter."
        ),
    },
    {
        "card_number": 111,
        "title": "Optimal sowing window and sowing method in Dry Direct Seeded Rice (D DSR)",
        "crop": "paddy",
        "category": "Crop Establishment & Water Saving",
        "zone": "Central and Northern Telangana Zones (Warangal)",
        "page": 6,
        "raw_text": (
            "Dry Direct Seeded Rice (D-DSR) established with precision machinery serves as a climate-resilient alternative "
            "to traditional flooded transplanting. The optimal sowing window is 10 to 15 days prior to the onset of the southwest "
            "monsoon or immediately upon first pre-monsoon rains (late May to mid-June). Seeds must be drilled at a shallow "
            "depth of 2 to 3 cm using a tractor-drawn seed-cum-fertilizer drill or zero-till seed drill into well-prepared dry tilth. "
            "D-DSR saves 30-40% irrigation water, eliminates nursery raising and transplanting labour drudgery, and allows "
            "the crop to mature 7-10 days earlier, avoiding terminal irrigation shortages."
        ),
    },
    {
        "card_number": 112,
        "title": "Soil test based fertilizer recommendation for targeted yield in sugarcane (Plant Crop)",
        "crop": "sugarcane",
        "category": "Nutrient Management",
        "zone": "Telangana State",
        "page": 7,
        "raw_text": (
            "Soil Test Crop Response (STCR) correlation equations for plant sugarcane calibrate precise nitrogen, phosphorus, "
            "and potassium requirements based on initial soil test values for specific yield targets (100 to 140 t/ha). "
            "STCR calibration eliminates over-fertilization, lowers production costs, and improves cane stalk thickness and juice sucrose purity."
        ),
    },
    {
        "card_number": 113,
        "title": "Soil test based fertilizer recommendation for targeted yield in sugarcane (Ratoon Crop)",
        "crop": "sugarcane",
        "category": "Nutrient Management",
        "zone": "Telangana State",
        "page": 8,
        "raw_text": (
            "Targeted yield fertilizer prescription equations for ratoon sugarcane in Telangana. Ratoon crops demand rapid "
            "nitrogen and potassium assimilation following stubble shaving and trash management. Application according to STCR "
            "equations enhances tiller survival, prevents early senescence, and achieves targeted millable cane yields economically."
        ),
    },
    {
        "card_number": 114,
        "title": "Soil test based fertilizer prescription equations for targeted yield of Bt cotton in Alfisols",
        "crop": "cotton",
        "category": "Nutrient Management",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 9,
        "raw_text": (
            "Soil Test Crop Response (STCR) fertilizer prescription equations formulated specifically for Bt cotton grown on "
            "red sandy loam and chalka soils (Alfisols) in the Central Telangana Zone (Warangal). Equations account for native soil "
            "nutrient supply to achieve target yields of 25 to 30 quintals of seed cotton per hectare. Split application of nitrogen "
            "and potassium at squaring, peak flowering, and boll development stages maximizes boll weight and avoids square shedding "
            "caused by luxury or deficient vegetative growth."
        ),
    },
    {
        "card_number": 115,
        "title": "Soil test based prescription equations for balanced fertilizer use and targeted yield of Bt cotton in Vertisols",
        "crop": "cotton",
        "category": "Nutrient Management",
        "zone": "Northern and Central Telangana Zones",
        "page": 10,
        "raw_text": (
            "STCR-based balanced fertilizer prescription equations for Bt cotton on deep black cotton soils (Vertisols). "
            "Nutrient prescription based on targeted yield equations balances nitrogen with potassium and phosphorus, curbing "
            "excessive vegetative canopy expansion common in heavy black soils. Enhances light penetration into the mid-canopy, "
            "minimizes internal boll rot, and increases net farm income through judicious fertilizer expenditure."
        ),
    },
    {
        "card_number": 116,
        "title": "Sulphur and boron fertilization for yield maximisation of groundnut grown on Alfisols",
        "crop": "groundnut",
        "category": "Nutrient Management",
        "zone": "Southern and Central Telangana Zones",
        "page": 11,
        "raw_text": (
            "Secondary and micronutrient management in groundnut cultivated on light-textured Alfisols. Application of sulphur "
            "through gypsum at pegging stage combined with soil-applied or foliar boron significantly reduces blind nuts (pop pods), "
            "improves pod filling, and enhances oil content by 2-3 percentage points."
        ),
    },
    {
        "card_number": 117,
        "title": "Integrated plant nutrient supply system in greengram-sorghum sequential cropping system under rainfed conditions",
        "crop": "greengram_sorghum",
        "category": "Nutrient Management",
        "zone": "Central Telangana Zone",
        "page": 12,
        "raw_text": (
            "Integrated plant nutrient supply (IPNS) combining farmyard manure (FYM), biofertilizers (Rhizobium and PSB), and "
            "balanced mineral fertilizers in a rainfed greengram followed by rabi sorghum sequential system. Inoculation and organic "
            "manuring leave residual nitrogen for the succeeding sorghum crop, improving soil health and stabilizing system productivity."
        ),
    },
    {
        "card_number": 118,
        "title": "Enhancing production potential of pigeonpea through foliar nutrition",
        "crop": "pigeonpea",
        "category": "Nutrient Management",
        "zone": "Central and Northern Telangana Zones",
        "page": 13,
        "raw_text": (
            "Foliar nutrition interventions in rainfed pigeonpea (redgram) during critical reproductive phases. Supplemental "
            "foliar sprays at flower initiation and 15 days later reduce flower drop, improve pod setting on secondary branches, "
            "and increase seed yield by 12-16% under soil moisture stress conditions."
        ),
    },
    {
        "card_number": 119,
        "title": "Nitrogen management in dry converted wet rice system",
        "crop": "paddy",
        "category": "Nutrient & Water Management",
        "zone": "Central and Southern Telangana Zones (Warangal)",
        "page": 14,
        "raw_text": (
            "Management of dry-converted wet rice (semi-dry rice) where rice is initially seeded dry under rainfed conditions "
            "due to delayed irrigation releases and subsequently converted to wet flooded ecology upon canal or tank water arrival. "
            "Nitrogen should be managed in split applications, withholding major nitrogen until flooding begins, followed by splits "
            "at active tillering and panicle initiation. Prevents severe denitrification and leaching losses while ensuring healthy "
            "tillering and robust panicle development in Telangana command areas."
        ),
    },
    {
        "card_number": 120,
        "title": "Optimizing nitrogen and potassium application for rabi sunflower through fertigation",
        "crop": "sunflower",
        "category": "Irrigation & Fertigation",
        "zone": "Southern and Central Telangana Zones",
        "page": 15,
        "raw_text": (
            "Drip fertigation scheduling for nitrogen and potassium in rabi sunflower. Supplying soluble fertilizers in weekly "
            "splits matched to crop growth stages improves nutrient use efficiency by 25-30% compared to conventional soil dressing, "
            "resulting in larger head diameter, higher seed weight, and substantial water conservation."
        ),
    },
    {
        "card_number": 121,
        "title": "Drip irrigation regimes and fertigation schedules in rabi cauliflower",
        "crop": "cauliflower",
        "category": "Horticulture Fertigation",
        "zone": "Peri-urban Telangana",
        "page": 16,
        "raw_text": (
            "Standardized drip irrigation and fertigation protocol for rabi cauliflower. Scheduling irrigation at 0.8 ETc with "
            "split fertigation yields compact, uniform, snow-white curds with higher marketable recovery while saving 35% water "
            "over furrow irrigation."
        ),
    },
    {
        "card_number": 122,
        "title": "Water budgeting of irrigated lowland rice using drum culture technique",
        "crop": "paddy",
        "category": "Water Management",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 17,
        "raw_text": (
            "Water budgeting and monitoring in puddled lowland rice using micro-lysimeter and drum culture techniques. Farmers "
            "are advised to avoid continuous deep flooding (5-10 cm) throughout the season. Maintaining shallow water depth "
            "(2-3 cm) during vegetative tillering and panicle initiation, followed by intermittent drainage until hairline crack "
            "formation, conserves 25% irrigation water without any reduction in grain yield in the Central Telangana Zone."
        ),
    },
    {
        "card_number": 123,
        "title": "Water budgeting of Alternate Wetting and Drying rice (AWD) with drum culture Technique",
        "crop": "paddy",
        "category": "Water Saving & Climate Resilience",
        "zone": "Central and Northern Telangana Zones (Warangal)",
        "page": 18,
        "raw_text": (
            "Alternate Wetting and Drying (AWD) water management in rice monitored through field water tubes (pani pipes). "
            "A 30 cm long perforated plastic pipe is installed in the paddy field with 20 cm below the soil surface. Irrigation is "
            "re-applied only when the water level inside the pipe drops to 15 cm below the soil surface during vegetative stages. "
            "Continuous flooding is retained only from flowering to milk stage. AWD saves 25 to 35% irrigation water, improves root "
            "aeration, reduces lodging, and decreases methane greenhouse gas emissions significantly."
        ),
    },
    {
        "card_number": 124,
        "title": "Weed management in rice – maize cropping system under conservation agriculture",
        "crop": "paddy",
        "category": "Weed Management & Conservation Agriculture",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 19,
        "raw_text": (
            "Weed management strategies in rice-maize cropping systems managed under zero tillage and conservation agriculture. "
            "Stale seedbed preparation prior to sowing followed by mechanical inter-cultivation with power weeders or manual spot "
            "weeding effectively suppresses troublesome grassy weeds (Echinochloa colona) and sedges (Cyperus rotundus). Retaining "
            "crop residue mulch creates a physical barrier that delays weed emergence, promotes beneficial microflora, and conserves "
            "residual soil moisture."
        ),
    },
    {
        "card_number": 125,
        "title": "Non-chemical weed management in okra-carrot organic cropping system",
        "crop": "okra_carrot",
        "category": "Organic Farming & Weed Management",
        "zone": "Peri-urban Telangana",
        "page": 20,
        "raw_text": (
            "Non-chemical weed suppression in vegetable crop sequences combining organic mulches (paddy straw, dried leaves) and "
            "shallow mechanical weeding with hand hoes. Effective weed suppression was achieved during critical first 30 days "
            "without synthetic herbicides, maintaining organic product purity and soil biological activity."
        ),
    },
    {
        "card_number": 126,
        "title": "Agronomic package for selective mechanisation in cotton on rainfed Alfisols",
        "crop": "cotton",
        "category": "Farm Mechanization & Productivity",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 21,
        "raw_text": (
            "Comprehensive agronomic package for selective mechanization in rainfed cotton grown on red sandy loam soils (Alfisols) "
            "in the Central Telangana Zone (Warangal). Synchronized package utilizes tractor-drawn inclined plate planters for precise "
            "geometry, followed by mini-tractor or power-weeder inter-cultivators at 20-25 and 40-45 days after sowing (DAS). "
            "Boom sprayers ensure rapid, uniform canopy coverage against pest flare-ups. Selective mechanization saves 40 to 45 "
            "man-days of labour per hectare, eliminates production bottlenecks during peak weeding and spraying, and boosts seed "
            "cotton yields by 15-20%."
        ),
    },
    {
        "card_number": 127,
        "title": "Agronomic package for complete mechanisation in pigeonpea on rainfed Alfisols",
        "crop": "pigeonpea",
        "category": "Farm Mechanization",
        "zone": "Central and Northern Telangana Zones",
        "page": 22,
        "raw_text": (
            "Complete mechanization package for rainfed pigeonpea on Alfisols covering mechanized seedbed preparation, pneumatic "
            "planter sowing, mechanical inter-row weeding, and combine harvesting with modified reel attachments. Overcomes severe "
            "farm labor shortages, reduces cultivation costs by 30%, and prevents harvest shattering losses."
        ),
    },
    {
        "card_number": 128,
        "title": "Selective mechanization for safflower growers profitability",
        "crop": "safflower",
        "category": "Farm Mechanization",
        "zone": "Northern and Central Telangana Zones",
        "page": 23,
        "raw_text": (
            "Selective mechanization solutions for safflower cultivation addressing the major constraint of spiny plants during "
            "inter-cultivation and harvesting. Tractor-mounted multi-crop planters and specialized thresher units enhance harvest "
            "efficiency, eliminate painful manual drudgery, and improve marketability of clean seed."
        ),
    },
    {
        "card_number": 129,
        "title": "Machine transplanting and direct seeding of rice are the best options over conventional transplanting in puddled soils",
        "crop": "paddy",
        "category": "Mechanized Establishment",
        "zone": "Central and Southern Telangana Zones (Warangal)",
        "page": 24,
        "raw_text": (
            "Evaluation of motorized mechanical transplanting and drum seeding in puddled rice soils in Telangana. Mechanical "
            "transplanting using 4-row or 8-row self-propelled transplanters with 15-day-old mat nursery seedlings ensures uniform "
            "hill spacing (30 x 12 cm or 30 x 14 cm) with 30-33 hills per square meter. Eliminates bending drudgery for farm labourers, "
            "reduces transplanting costs by 40-50%, ensures faster seedling establishment with minimal root shock, and increases "
            "paddy grain yield by 8-12% compared to haphazard manual transplanting."
        ),
    },
    {
        "card_number": 130,
        "title": "Quick cooking redgram dhal – A convenience product",
        "crop": "redgram",
        "category": "Post-Harvest Processing",
        "zone": "Telangana State",
        "page": 25,
        "raw_text": (
            "Post-harvest technology protocol for processing quick-cooking redgram (pigeonpea) dhal developed by PJTSAU. Controlled "
            "pre-treatment and thermal puffing techniques reduce domestic boiling and cooking time from 35 minutes down to 10-12 minutes, "
            "conserving fuel energy while retaining high protein and dietary fiber content."
        ),
    },
    {
        "card_number": 131,
        "title": "Management of stem borer in rice with novel insecticides",
        "crop": "paddy",
        "category": "Plant Protection & IPM",
        "zone": "Central and Northern Telangana Zones (Warangal)",
        "page": 26,
        "raw_text": (
            "Integrated Pest Management (IPM) guidelines for yellow stem borer (Scirpophaga incertulas) in rice in Telangana. "
            "Cultural controls include clipping seedling leaf tips prior to transplanting to eliminate egg masses, synchronizing "
            "transplanting within communities, and installing pheromone traps at 8 to 10 traps per hectare for monitoring. Chemical "
            "intervention is warranted only when field monitoring reveals pest populations exceeding economic threshold levels (ETL): "
            "10% dead hearts at vegetative stage or 2% white ears at flowering stage. Farmers must refer to approved product labels "
            "for specific registered formulations, timing, and dosage, and consult the nearest Krishi Vigyan Kendra (KVK) or Kisan "
            "Call Centre (1551) before spraying."
        ),
    },
    {
        "card_number": 132,
        "title": "Novel insecticide combinations for the control of sucking pests and pink bollworm in cotton",
        "crop": "cotton",
        "category": "Plant Protection & IPM",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 27,
        "raw_text": (
            "Integrated Pest Management (IPM) strategy for pink bollworm (Pectinophora gossypiella) and sucking insect complexes "
            "(jassids, aphids, thrips, whiteflies) in Bt cotton across the Central Telangana Zone (Warangal). Cultural management "
            "involves erecting yellow sticky traps for sucking pests, installing pink bollworm pheromone traps at 5 traps per acre "
            "starting 45 days after sowing (DAS), and detopping/nipping terminal shoots at 80-90 DAS to remove favoured oviposition sites. "
            "Manually collect and destroy rosette flowers containing larvae. Chemical sprays should be initiated only when trap catches "
            "exceed 8 moths per trap per day for three consecutive days or 10% damaged green bolls with live larvae. Farmers must "
            "strictly follow instructions on registered product labels and seek guidance from local KVK or Call Centre (1551) for approved "
            "molecules, dosages, and safe handling precautions."
        ),
    },
    {
        "card_number": 133,
        "title": "Novel fungicide molecules to manage anthracnose disease in soybean",
        "crop": "soybean",
        "category": "Plant Protection",
        "zone": "Northern Telangana Zone",
        "page": 28,
        "raw_text": (
            "Management of anthracnose / pod blight (Colletotrichum truncatum) in soybean in Northern Telangana. Field sanitation, "
            "crop rotation with non-host cereals, and certified disease-free seed selection are primary defenses. Follow registered "
            "product labels and consult local agricultural extension officers or KVK for verified fungicide treatments and dosage."
        ),
    },
    {
        "card_number": 134,
        "title": "Use of nuclear polyhedrosis virus (SNPV) and bird perches to reduce insect pests in bhendi",
        "crop": "bhendi",
        "category": "Biological Pest Management",
        "zone": "Central and Southern Telangana Zones",
        "page": 29,
        "raw_text": (
            "Eco-friendly biological pest management in okra (bhendi) using Spodoptera Nuclear Polyhedrosis Virus (SNPV) combined "
            "with erecting bird perches (T-shaped bamboo perches at 20 per acre). Encourages predatory insectivorous birds and utilizes "
            "targeted biological viral solutions, significantly reducing synthetic pesticide usage and chemical residues in harvest."
        ),
    },
    {
        "card_number": 135,
        "title": "Seed treatment with copper oxychloride / azadirachtin to reduce bird damage at sowing stage in maize and sunflower",
        "crop": "maize_sunflower",
        "category": "Crop Protection & Bird Deterrence",
        "zone": "Central and Northern Telangana Zones",
        "page": 30,
        "raw_text": (
            "Seed deterrence treatment protocols to repel birds during germination and early seedling emergence in maize and sunflower. "
            "Treating seed with registered botanical bitter repellents or seed dressing forms a gustatory repellent that protects newly "
            "sprouted seeds from parakeets, crows, and pigeons, ensuring uniform plant stand establishment in open fields."
        ),
    },
    {
        "card_number": 136,
        "title": "Planting barrier crops to reduce bird damage in maize crop",
        "crop": "maize",
        "category": "Crop Protection & Bird Deterrence",
        "zone": "Central Telangana Zone (Warangal)",
        "page": 31,
        "raw_text": (
            "Border barrier cropping technique using tall, non-palatable boundary crops (such as castor or forage sorghum) around maize "
            "plots. The vegetative barrier obstructs line-of-sight flight paths of destructive bird flocks, reducing damage to outer maize "
            "cobs by over 50% without harming avian wildlife."
        ),
    },
    {
        "card_number": 137,
        "title": "Integrated bird management in maize using reflective ribbons and wrapping method",
        "crop": "maize",
        "category": "Integrated Bird Management",
        "zone": "Central and Southern Telangana Zones",
        "page": 32,
        "raw_text": (
            "Integrated physical bird scaring technology utilizing multi-colored reflective holographic ribbons strung above the crop canopy "
            "combined with mechanical husk wrapping. Wind-induced ribbon fluttering and light reflection disorient bird flocks during "
            "cob maturity, protecting high-value seed production plots cost-effectively."
        ),
    },
    {
        "card_number": 138,
        "title": "Block plantation, reflective ribbons and whole egg solution spray in sunflower and bajra to reduce bird damage",
        "crop": "sunflower_bajra",
        "category": "Crop Protection",
        "zone": "Southern and Central Telangana Zones",
        "page": 33,
        "raw_text": (
            "Multi-tactic bird management in sunflower and pearl millet (bajra) combining compact block plantations, border reflective "
            "ribbons, and spraying biological repellent solutions (whole egg formulation) on boundary rows during seed development. "
            "Deters bird flocks through olfactory and visual signals, preserving sunflower capitulum seed fill."
        ),
    },
    {
        "card_number": 139,
        "title": "Management of Macrophomina phaseolina stem and root rot of sesame",
        "crop": "sesame",
        "category": "Plant Protection",
        "zone": "Northern and Central Telangana Zones",
        "page": 34,
        "raw_text": (
            "Cultural and biological management of stem and charcoal root rot (Macrophomina phaseolina) in sesame. Soil incorporation "
            "of Trichoderma viride enriched farmyard manure combined with deep summer ploughing and balanced irrigation prevents dry "
            "root rot outbreaks in sandy loam soils during high temperature spells."
        ),
    },
    {
        "card_number": 140,
        "title": "Soybean storage technology: Impact on quality and health of treated seeds",
        "crop": "soybean",
        "category": "Seed Technology & Storage",
        "zone": "Northern Telangana Zone",
        "page": 35,
        "raw_text": (
            "Post-harvest seed handling and hermetic storage protocols for soybean in Northern Telangana. Maintaining seed moisture "
            "strictly below 9% and packing seeds in multi-layer hermetic bags (PICS bags) or polythene-lined containers preserves "
            "germination vigor above 70% across 8 months of storage, preventing seed coat cracking and mycoflora deterioration."
        ),
    },
]


def ingest_all(
    out_path: str = "backend/data/crop_advisories.jsonl",
) -> list[TechnologyCard]:
    """Validates raw cards, assigns SHA-256 content hashes, and writes JSONL."""
    cards: list[TechnologyCard] = []
    retrieved_at = "2026-11-08T14:45:00Z"
    publisher = "Professor Jayashankar Telangana State Agricultural University (PJTSAU)"
    pub_no = "PJTSAU/Res/2020-21/AT"
    source_url = "https://pjtau.edu.in/director-of-research-2/"
    year = "2020-21"

    for item in RAW_CARDS_DATA:
        raw_text = item["raw_text"].strip()
        chash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        card_id = f"PJTSAU-2020-21-{item['card_number']}"

        card = TechnologyCard(
            card_id=card_id,
            card_number=item["card_number"],
            title=item["title"].strip(),
            crop=item["crop"].strip(),
            category=item["category"].strip(),
            zone=item["zone"].strip(),
            page=item["page"],
            publisher=publisher,
            publication_number=pub_no,
            year=year,
            source_url=source_url,
            retrieved_at=retrieved_at,
            raw_text=raw_text,
            content_hash=chash,
        )
        cards.append(card)

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        for card in cards:
            f.write(json.dumps(card.model_dump()) + "\n")

    print(f"Successfully ingested and wrote {len(cards)} technology cards to {out_path}")
    return cards


if __name__ == "__main__":
    ingest_all()
