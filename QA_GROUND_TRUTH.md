# QA Ground Truth Evaluation

This document contains manually verified ground truth for evaluating the **Tasmania Fishing Assistant** chatbot.

---

## Table of Contents
- [Baseline Questions (8)](#baseline-questions-8)
- [Difficult Questions (2)](#difficult-questions-2)
- [Summary](#summary)
- [Evaluation Methodology](#evaluation-methodology)
- [Files Used](#files-used)

---

## Baseline Questions (8)

These questions test the three core scenarios: **RAG only**, **Tool only**, and **RAG + Tool**.

---

### P1: Fishing information for a specific species

**Question**: *What is the bag limit, minimum size for brown trout?*

**Type**: RAG (Document Retrieval)

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/species`
- **Citation Location**: Species section (Trout – Brown)
- **Citation Text**:
  ```
  "Trout - Brown": {
    "Scientific name": "Salmo trutta",
    "liciense required": false,
    "Season": "Open all year",
    "Bag Limit": "12",
    "Possession Limit": "24",
    "Minimum size": "No minimum size",
    "Grows to": "Up to 1.4 metres and 23 kg",
    "Identifying features": "Sea run fish are uniformly brownish though may appear silvery with slightly darker, metallic grey back and faint dark spots on the sides, dorsal fins and gill covers with a paler underside. Estuarine fish are sometimes brown to olive green with bolder spotting. Most spots are surrounded by a paler halo and the tail has very few if any spots. The jaw extends beyond the eye.",
    "Habitat": "Introduced from England in 1864 and quickly spread to most rivers and lakes across the state. They thrive in shallow areas feeding on worms and invertebrates.",
    "Fishing information": "This species is managed by the Inland Fisheries Service. It is found in most estuaries around Tasmania and taken by an array of natural and artificial lures and sometimes in gillnets."
  },
  ```
- **Correct Answer**: **Bag limit:** 12; **Minimum size:** No minimum size

**Route Decision**: RAG

**System Response**
> Hey there! 🎣 You're looking for information on brown trout in Tasmania. Here's what the official documents say:
>
>  *   **Bag Limit:** 12
>  *   **Minimum size:** No minimum size
>
>  This information comes directly from the `[Source: tas_fishing_guide/species]` document.
>
>  Happy fishing! 🐟 Always double-check current regulations before heading out.
>
>  **What else can I help with?**
>  * 💡 Want to know size limits too?
>  * 📍 Need good locations for this species?

**Verify Retrieval**
- ✓ `'12'` found in retrieved documents
- ✓ `'trout - brown'` found in retrieved documents

**Status**: ✅ **PASSED**

---

### P2: Fishing licence information

**Question**: *Do I need a licence for fishing abalone?*

**Type**: RAG

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/fishing_licence`
- **Citation Location**: Fishing licence section
- **Citation Text**:
  ```
  "licence_types": [
    {
      "name": "Rock Lobster Pot, Ring or Dive",
      "age_restriction": "Not available to children under 10 years",
      "check_before_buying": ["season dates", "rules and catch limits"]
    },
    {
      "name": "Abalone",
      "age_restriction": "Not available to children under 10 years",
      "check_before_buying": ["abalone rules and catch limits"]
    }
  ]
  ```
- **Correct Answer**: **Yes**, you need an abalone licence.

**Route Decision**: RAG

**System Response**
>Yes, you generally need a licence for fishing abalone in Tasmania! 🎣
>
>Here's what the official documents say:
>
>*   **Licence Required** ✅: There is a specific "Abalone" licence type listed under the available licences [Source: >tas_fishing_guide/fishing_licence].
>*   **Age Restriction**: This licence is "Not available to children under 10 years" [Source: tas_fishing_guide/fishing_licence].
>*   **What to Check**: Before you buy your abalone licence, it's a good idea to "check before buying: ['abalone rules and catch >limits']" [Source: tas_fishing_guide/fishing_licence].
>*   **Exemption**: Aboriginal fishers are exempt from holding a licence for fishing [Source: tas_fishing_guide/fishing_licence].
>
>Always make sure to check the abalone rules and catch limits before you head out!

**Verify Retrieval**
- ✓ `'licence'` found in retrieved documents
- ✓ `'abalone'` found in retrieved documents

**Status**: ✅ **PASSED**

---

### P3: Fishing location information

**Question**: *Where are good spots for flathead fishing?*

**Type**: RAG

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/hot_fishing_spots`
- **Citation Location**: Hot fishing spots section
- **Citation Text (excerpt of regions)**:
  ```
  "name": "Derwent River",
  "name": "East Coast Region",
  "name": "St Helens Region",
  "name": "Bruny D'Entrecasteaux Region",
  "name": "Tasman Peninsula Region (turrakana)",
  "name": "North East Coast and Flinders Island",
  "name": "Tamar River (kanamaluka)",
  "name": "Devonport and Port Sorell Region",
  "name": "North West Coast",
  "name": "King Island",
  ```
- **Correct Answer**: Provide notable regions (e.g., Tamar River, Derwent River, etc.) and typical shore/boat points.

**Route Decision**: RAG

**System Response**
> Hello there! 🎣 You're in luck, Tasmania has many great spots for flathead fishing! Based on the official documents, here are some excellent locations across different regions where you can target flathead:
>
> **Tamar River (kanamaluka)** (for Sand flathead from shore)
> * Greens Beach
> * Kelso Jetty
> * Clarence Point
> * Beauty Point Wharf
> * Sidmouth
> * Deviot Pontoon
> * Hillwood
> * George Town
> * Low Head Pilot Station
> * Beechford
> * Weymouth
> * Bellingham
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **Devonport and Port Sorell Region** (for Sand flathead from shore, Bluespotted flathead from boat)
> * Bakers Beach
> * Squeaking Point Jetty
> * Port Sorell Jetty
> * Moorlands Beach
> * Reg Hope Park
> * Horsehead Creek
> * Mussel Rock Lighthouse
> * Mersey Bluff
> * Don Heads
> * Turners Beach
> * Leven River
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **Tasman Peninsula Region (turrakana)** (for Sand flathead from shore, Tiger flathead from boat)
> * Cremorne Narrows
> * McGees Bridge
> * Lewisham
> * Carlton River
> * Primrose Sands
> * Dunalley Canal
> * Marion Bay Spit
> * Pirates Bay Jetty
> * Fortescue Bay
> * Port Arthur
> * White Beach
> * Nubeena
> * Taranna
> * Frederick Henry Bay (commonly caught here)
> * Norfolk Bay (commonly caught here)
> * Blackman Bays (commonly caught here)
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **North East Coast and Flinders Island** (for Sand flathead from shore)
> * Bridport
> * Waterhouse
> * Tomahawk
> * Petal Point
> * Little Musselroe Bay
> * Great Musselroe Bay
> * Eddystone Point
> * Ansons Bay
> * Whitemark Wharf
> * Lady Barron Wharf
> * Settlement Point
> * Palana
> * North East River
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **Derwent River** (for Sand flathead from shore)
> * Dowsing Point
> * Botanical Gardens
> * Tasman Bridge
> * Regatta Grounds
> * Sandy Bay
> * Taroona
> * Alum Cliffs
> * Browns River
> * Kingston
> * Blackmans Bay
> * South Arm Jetty
> * Opossum Bay Jetty
> * Ralphs Bay
> * Bellerive Bluff
> * Lindisfarne
> * Otago Bay
> * Old Beach
> * Bridgewater
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **East Coast Region** (for Sand flathead from shore, Tiger flathead from boat)
> * Waubs Bay
> * The Gulch Wharf
> * Coles Bay Jetty
> * Swanwick
> * Swansea Pier
> * Little Swanport
> * Triabunna
> * Prosser River
> * Earlham Lagoon
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **St Helens Region** (for Sand flathead from shore, Tiger flathead from boat)
> * St Helens Wharf
> * Beauty Bay
> * Kirwans Beach
> * Talbot Street
> * Cunninghams Jetty
> * Stieglitz Jetty
> * Akaroa
> * Burns Bay
> * Maurouard Beach
> * Dora Point
> * Binalong Bay
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **Bruny D'Entrecasteaux Region** (for Sand flathead from shore)
> * Dru Point
> * Margate Wharf
> * Kettering
> * Woodbridge
> * Roberts Point
> * Dennes Point
> * Adventure Bay
> * Cloudy Bay Lagoon
> * Gordon Jetty
> * Trial Bay
> * Huon Estuary
> * Southport
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **North West Coast** (for Flathead from shore, Bluespotted flathead from boat)
> * Burnie Boat Ramp
> * Cooee Point
> * Doctors Rocks
> * Wynyard Wharf
> * Boat Harbour
> * Sisters Beach
> * Rocky Cape
> * Stanley Wharf
> * East Inlet
> * West Inlet
> * Godfrey's Beach
> * Duck Bay
> * Montagu
> * Arthur River
> * Marrawah
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> **King Island** (for Sand flathead from shore, Bluespotted flathead from boat)
> * Grassy Jetty
> * Bold Head
> * Naracoopa Jetty
> * Sea Elephant
> * Lavinia Point
> * Three Sisters
> * Phoques Bay
> * Currie
> * British Admiral Point
>   *(Source: tas_fishing_guide/hot_fishing_spots)*
>
> Happy fishing! 🐟 Always check for any specific bag limits or size restrictions before you go.
>
> **What else can I help with?**
> • 🌤️ Would you like the weather forecast for this location?  
> • 🐟 Want to know what species are there?

**Verify Retrieval**
- ✓ Sections retrieved from `tas_fishing_guide/hot_fishing_spots`
- ✓ `'flathead'` found in retrieved documents

**Status**: ✅ **PASSED**

---

### P4: Weather forecast for a certain day

**Question**: *What’s the weather like for fishing at Hobart tomorrow?*

**Type**: Tool (Weather API)

**Manual Ground Truth**
- **Tool**: `get_fishing_weather`
- **Parameters**:
  ```json
  {
    "location": "Hobart",
    "days": 1
  }
  ```
- **Correct Answer**: Provide tomorrow’s forecast and a brief fishing suitability note.

**Route Decision**: TOOL

**System Response**
>Tomorrow, October 19, looks excellent for fishing in Hobart! ✨ You can expect clear skies with an average temperature of 14.7°C. Winds will be around 24.3 km/h, and there's no rain expected (0.0mm). The fishing score for the day is 9/10.

**Status**: ✅ **PASSED**

---

### P5: Weather forecast for a period (next 5 days)

**Question**: *Which day will have the best fishing weather in Hobart next week?*

**Type**: Tool (Weather API)

**Manual Ground Truth**
- **Tool**: `get_fishing_weather`
- **Parameters**:
  ```json
  {
    "location": "Hobart",
    "days": 5
  }
  ```
- **Correct Answer**: Rank the next 5 days by fishing conditions and recommend the best day(s).

**Route Decision**: TOOL

**System Response**
> Great week ahead for fishing in Hobart! 🎣
>
> **Best Day: Sunday, October 19** – Excellent conditions ✨  
> * **Conditions**: clear sky  
> * **Temperature**: 14.7 °C  
> * **Wind**: 24.3 km/h  
> * **Rain**: 0.0 mm  
> * **Score**: 9/10  
>
> Other good days for fishing:  
> * **Tuesday, Oct 21** (score 8) – Overcast clouds, lighter wind (11.8 km/h)  
> * **Thursday, Oct 23** (score 7) – Light rain, moderate wind (15.1 km/h)

**Status**: ✅ **PASSED**

---

### P6: Legal size check – undersized fish

**Question**: *Is 30 cm flathead legal to keep?*

**Type**: RAG

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/species`
- **Citation Location**: Flathead species entries (Sand, Rock, Bluespotted, Tiger)
- **Citation Text (excerpt)**:
  ```
  "Flathead - Bluespotted": { "Minimum size": "40cm", ... },
  "Flathead - Rock": { "Minimum size": "40cm", ... },
  "Flathead - Sand": { "Minimum size": "All waters (except King and Flinders Islands): Minimum size 35cm , maximum size 40cm", ... },
  "Flathead - Tiger": { "Minimum size": "32cm", ... }
  ```
- **Correct Answer**: **No** — 30 cm is under the minimum size for these species.

**Route Decision**: RAG

**System Response**
> Hey there! 🎣 Let's dive into the rules for keeping flathead in Tasmania based on your fishing guide.  
>
> Based on the official documents provided, a 30 cm flathead is **not legal to keep** for any of the flathead species listed:  
>
> * **Tiger Flathead:** The minimum size for a Tiger Flathead is 32 cm. *(Source: tas_fishing_guide/species)*  
> * **Rock Flathead:** The minimum size for a Rock Flathead is 40 cm. *(Source: tas_fishing_guide/species)*  
> * **Sand Flathead:** For Sand Flathead, in all waters (except King and Flinders Islands), the minimum size is 35 cm, with a maximum size of 40 cm. *(Source: tas_fishing_guide/species)*  
>
> Since 30 cm is below the minimum size for all these commonly found flathead species, it would need to be released. 🐟  
>
> Always double-check the specific identification of your catch to ensure you're following the correct regulations!  
>
> **What else can I help with?**  
> • 📏 Want to check another fish size?  
> • 🎣 Need to know the bag limit?

**Verify Retrieval**
- ✓ Relevant species sections retrieved and matched
- ✓ `'Minimum size'` found in retrieved documents

**Status**: ✅ **PASSED**

---

### P7: Fishing information and weather forecast combined

**Question**: *What’s the weather like at Port Sorell and what species can I catch there?*

**Type**: RAG & TOOL

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/hot_fishing_spots`
- **Expected Tool + Params**: `get_fishing_weather` with `{ "location": "Port Sorell", "days": 5 }`
- **Citation Location**: Hot fishing spots (Devonport & Port Sorell Region)
- **Citation Text (excerpt)**:
  ```
  "name": "Devonport and Port Sorell Region",
  "popular_spots": ["Bakers Beach", "Squeaking Point Jetty", "Port Sorell Jetty", ...],
  "species": {
    "shore": ["Australian salmon", "Mullet", "Sand flathead", "Whiting", "Pike", "Cod"],
    "boat": ["Silver trevally", "Snapper", "Bluespotted flathead", "Snook", "Pike", "Blue warehou", "Tailor", "Gurnard", "Barracouta", "Mako shark", "Gummy shark (outside Shark Refuge Area)"]
  },
  "local_facts": [
    "Accessible shore fishing at Port Sorell and Squeaking Point jetties, Mersey Bluff and Leven River",
    "Large Australian salmon common from beaches and rocky headlands",
    "Emerging fishery for King George whiting, salmon, snapper and yellowtail kingfish in Port Sorell",
    "Port Sorell is a Shark Refuge Area",
    "Recreational gillnetting not allowed in Port Sorell estuary"
  ]
  ```
- **Correct Answer**: Provide the 5‑day weather plus expected species and key local rules.

**Route Decision**: RAG & TOOL

**System Response**
> Planning a fishing trip to Port Sorell, Tasmania? Here's what you need to know about the local regulations, species, and the upcoming weather forecast! 🎣
>
> 📍 **Fishing Rules and Species in Port Sorell**
>
> Port Sorell is part of the Devonport and Port Sorell Region, offering excellent fishing opportunities.
>
> ⚠️ **Important Regulations:**
> * Port Sorell is designated as a **Shark Refuge Area**. This means that taking sharks, skates, or rays is generally not allowed within the estuary, with the exception of Gummy shark *outside* the Shark Refuge Area (Source: tas_fishing_guide/hot_fishing_spots).
> * **Recreational gillnetting is not permitted** in the Port Sorell estuary (Source: tas_fishing_guide/hot_fishing_spots).
> * Shore fishing is easily accessible at Port Sorell and Squeaking Point jetties, Mersey Bluff, and the Leven River (Source: tas_fishing_guide/hot_fishing_spots).
>
> 🐟 **What You Can Catch:**
> * **From the Shore:** You can expect to catch Australian salmon, Mullet, Sand flathead, Whiting, Pike, and Cod. Large Australian salmon are particularly common from beaches and rocky headlands (Source: tas_fishing_guide/hot_fishing_spots).
> * **From a Boat:** Anglers venturing out in a boat can target Silver trevally, Snapper, Bluespotted flathead, Snook, Pike, Blue warehou, Tailor, Gurnard, Barracouta, Mako shark, and Gummy shark (remember, *outside* the Shark Refuge Area) (Source: tas_fishing_guide/hot_fishing_spots).
> * **Emerging Fisheries:** There's an emerging fishery in Port Sorell for King George whiting, salmon, snapper, and yellowtail kingfish (Source: tas_fishing_guide/hot_fishing_spots).
>
> 🌤️ **5-Day Weather Forecast for Port Sorell (October 19 - October 23, 2025)**
>
> Here's the upcoming weather to help you plan your trip:
>
> * **Sunday, October 19:** Expect light rain with an average temperature of 12.3°C (max 13.8°C, min 10.2°C). Winds will be around 18.5 km/h, and there'll be about 5.2 mm of rain. The fishing score for the day is 8.
> * **Monday, October 20:** The day will be overcast with an average temperature of 11.6°C (max 15.5°C, min 8.9°C). Winds will pick up slightly to 25.3 km/h, and there's a small chance of rain (0.1 mm). The fishing score is 8.
> * **Tuesday, October 21:** Look forward to scattered clouds and an average temperature of 11.6°C (max 14.8°C, min 8.0°C). Winds will be around 21.6 km/h, and importantly, no rain is expected. This day has an excellent fishing score of 9! ✨
> * **Wednesday, October 22:** Prepare for light rain again, with a cooler average temperature of 9.6°C (max 10.7°C, min 8.4°C). Winds will be lighter at 7.1 km/h, but rainfall is expected to be higher at 15.5 mm. The fishing score is 6.
> * **Thursday, October 23:** The sky will be clear with an average temperature of 10.2°C (max 15.1°C, min 6.2°C). Winds will be 17.3 km/h, and no rain is forecast. This day also boasts an excellent fishing score of 9! ✨
>
> The forecast recommends that **Tuesday, October 21**, and **Thursday, October 23** are your best days for fishing, both with an 'Excellent' rating. Tuesday will have scattered clouds and no rain, while Thursday will offer clear skies and no rain. Both days have favorable fishing scores of 9.
>
> ✅ **Overall Recommendation:**
> It looks like a great week for fishing in Port Sorell! With a variety of species available from both shore and boat, you'll have plenty of options. Remember to respect the Shark Refuge Area regulations and avoid gillnetting. Based on the forecast, **Tuesday, October 21** and **Thursday, October 23**, look like ideal days to cast your line with excellent fishing scores and pleasant weather conditions. Good luck! 🎣

**Verify Retrieval**
- ✓ `'Port Sorell'` found in retrieved documents

**Status**: ✅ **PASSED**

---

### P8: Fishing information and weather forecast combined

**Question**: *I want to go fishing for flathead at Burnie – what are the rules for flathead and what’s the weather forecast?*

**Type**: RAG & TOOL

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/species`
- **Expected Tool + Params**: `get_fishing_weather` with `{ "location": "Burnie", "days": 5 }`
- **Citation Location**: Flathead species entries (as in P6)
- **Correct Answer**: Provide flathead rules (min size, bag/possession limits by species/zone where relevant) plus 5‑day forecast.

**Route Decision**: RAG & TOOL

**System Response**
> Hello! Planning a fishing trip for flathead at Burnie sounds like a great idea. Here's a breakdown of the rules for flathead and the upcoming weather forecast for your trip.  
>
> **Fishing Rules and Regulations for Flathead 🎣**  
>
> There are a few types of flathead commonly caught in Tasmania. For fishing at Burnie, you'll most likely encounter **Sand Flathead** or potentially **Tiger Flathead**. Here are the rules for both:  
>
> **Sand Flathead (Platycephalus bassensis)**  
> * **License Required:** No ✅ (Source: tas_fishing_guide/species)  
> * **Season:** Open all year 📅 (Implied, no specific season mentioned)  
> * **Bag Limit (Northern/Western Zone):** 10 fish 🐟 (Source: tas_fishing_guide/species)  
> * **Possession Limit (Northern/Western Zone):** 10 fish 🎣 (Source: tas_fishing_guide/species)  
> * **Minimum Size (All waters except King and Flinders Islands):** 35 cm 📏  
> * **Maximum Size (All waters except King and Flinders Islands):** 40 cm 📏 (Source: tas_fishing_guide/species)  
> * **Habitat & Tips:** Sand flathead are bottom dwellers, preferring shallow waters (0–25 metres) with a weed-free, sandy bottom. They are the most commonly caught recreational species and are relatively easy to catch using a variety of baits and lures fished close to the bottom, often from a slowly drifting boat. (Source: tas_fishing_guide/species)  
>
> **Tiger Flathead (Neoplatycephalus richardsoni)**  
> * **License Required:** No ✅ (Source: tas_fishing_guide/species)  
> * **Season:** Open all year 📅 (Source: tas_fishing_guide/species)  
> * **Bag Limit:** 20 fish 🐟 (Source: tas_fishing_guide/species)  
> * **Possession Limit:** 30 fish 🎣 (Source: tas_fishing_guide/species)  
> * **Minimum Size:** 32 cm 📏 (Source: tas_fishing_guide/species)  
> * **Habitat & Tips:** Tiger flathead are generally found both inshore and on the continental shelf between 10 and 160 metres. While usually caught in deeper, offshore waters, they can occasionally be taken closer inshore using similar gear and techniques as for sand flathead. (Source: tas_fishing_guide/species)  
>
> **Weather Forecast for Burnie 🌤️**  
>
> Here's the 5-day weather forecast for Burnie, along with a fishing score for each day (a higher score indicates better fishing conditions based on temperature, wind, and rain):  
>
> * **Sunday, October 19:**  
>   * **Conditions:** Light rain 🌧️  
>   * **Temperature:** Average 12.9 °C (Min 11.6 °C, Max 14.0 °C)  
>   * **Wind Speed:** 18.5 km/h  
>   * **Rainfall:** 2.7 mm  
>   * **Fishing Score:** 8 (Good)  
>
> * **Monday, October 20:**  
>   * **Conditions:** Clear sky ✨  
>   * **Temperature:** Average 11.7 °C (Min 9.3 °C, Max 15.3 °C)  
>   * **Wind Speed:** 24.3 km/h  
>   * **Rainfall:** 0.0 mm  
>   * **Fishing Score:** 9 (Excellent)  
>
> * **Tuesday, October 21:**  
>   * **Conditions:** Scattered clouds ☁️  
>   * **Temperature:** Average 11.5 °C (Min 8.5 °C, Max 15.3 °C)  
>   * **Wind Speed:** 18.4 km/h  
>   * **Rainfall:** 0.0 mm  
>   * **Fishing Score:** 9 (Excellent)  
>
> * **Wednesday, October 22:**  
>   * **Conditions:** Light rain 🌧️  
>   * **Temperature:** Average 10.0 °C (Min 8.9 °C, Max 11.6 °C)  
>   * **Wind Speed:** 10.7 km/h  
>   * **Rainfall:** 12.2 mm  
>   * **Fishing Score:** 8 (Good)  
>
> * **Thursday, October 23:**  
>   * **Conditions:** Clear sky ✨  
>   * **Temperature:** Average 10.9 °C (Min 7.8 °C, Max 14.3 °C)  
>   * **Wind Speed:** 19.5 km/h  
>   * **Rainfall:** 0.0 mm  
>   * **Fishing Score:** 9 (Excellent)  
>
> **Overall Recommendation for Your Trip 🎣✨**  
>
> It looks like a great week ahead for fishing in Burnie!  
> The best days for fishing are **Monday, October 20**, **Tuesday, October 21**, and **Thursday, October 23**, all with an excellent fishing score of 9. Monday, October 20, is highlighted as the top pick with clear skies, an average temperature of 11.7 °C, and no rain.  
>
> **Tip:** When fishing for flathead, remember they prefer to stay close to the sandy bottom. Using a paternoster rig or soft plastics retrieved slowly along the bottom can be very effective! Good luck with your fishing! 🎣
**Verify Retrieval**
- ✓ Relevant flathead sections retrieved

**Status**: ✅ **PASSED**

---

## Baseline Tests Summary

| Test ID | Question Type | Status | Notes |
|---|---|---|---|
| P1 | RAG | ✅ Pass | Correct answer and citation |
| P2 | RAG | ✅ Pass | Licence requirement correctly identified |
| P3 | RAG | ✅ Pass | Comprehensive regions listed |
| P4 | Tool | ✅ Pass | Accurate single‑day forecast with score |
| P5 | Tool | ✅ Pass | Ranked 5‑day outlook with recommendation |
| P6 | RAG | ✅ Pass | Correct legal‑size reasoning across species |
| P7 | RAG & Tool | ✅ Pass | Species + 5‑day forecast + local rules |
| P8 | RAG & Tool | ✅ Pass | Flathead rules + 5‑day forecast |

**Overall Pass Rate**: **8/8 (100%)**

---

## Difficult Questions (2)

These questions test the system’s limitations and error‑handling.

---

### D1: Out of scope – fishing techniques/timing

**Question**: *What’s the best time of day to catch yellowtail kingfish under the Tasman Bridge?*

**Type**: Out of Scope (Information Not Available)

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/hot_fishing_spots`
- **What IS in documents**: A local fact notes a **summer run of yellowtail kingfish** up to the Tasman Bridge.
- **What is NOT in documents**: Best time of day, techniques/tactics, seasonal timing beyond “summer run”.
- **Correct Answer**: Acknowledge location/season context; **state that time‑of‑day info isn’t in the documents**.

**System Response**
> Searching for the perfect time to reel in some yellowtail kingfish under the Tasman Bridge? Here's what the provided information tells us! 🎣  
>
> ### Fishing Information 🐟  
> According to the `tas_fishing_guide/hot_fishing_spots`, the Tasman Bridge is a popular spot in the Derwent River region for boat fishing, and yellowtail kingfish are among the species you can target there.  
> While the documents confirm a "Summer run of yellowtail kingfish under the headlands as far as the Tasman Bridge," they do not specify the best *time of day* to catch them.  
> This local fact indicates that **summer** is the prime season for these fish in that area.  
>
> ### Weather Forecast ⚠️  
> Unfortunately, I can't provide a weather forecast at the moment. My weather tool encountered an error and is unable to access the forecast.  
> Please try again later for an updated weather report for your fishing trip.  
>
> ### Overall Recommendation for Your Trip 📍  
> Given the information, your best bet for catching yellowtail kingfish under the Tasman Bridge is during the **summer season**.  
> While the specific best time of day isn't mentioned in these documents, many anglers find success targeting predatory fish like kingfish during periods of active feeding — often around **dawn or dusk**, or when **tidal movements are strong**.  
>
> Since the weather forecast is currently unavailable, remember to check local conditions before you head out.  
>
> Good luck on your fishing adventure! Perhaps checking with local tackle shops or experienced anglers in the area could provide more precise tips on the best time of day for kingfish under the Tasman Bridge. 🎣

**System Verification**
- Router → RAG ✅  
- Retrieved relevant context ✅  
- Recognised information gap ✅  
- Communicated limitation clearly ✅

**Status**: ✅ **Handled Appropriately**

---

### D2: Complex regulation – multi‑zone question

**Question**: *If I fish in both the Eastern and Western zones in one day, what’s my rock lobster limit?*

**Type**: Complex Regulation (Multi‑part Rules)

**Manual Ground Truth**
- **Expected Source**: `tas_fishing_guide/species`
- **Citation Text (excerpt)**:
  ```
  Daily bag limit:
  Eastern Region – 2 rock lobster
  Western Region – 5 rock lobster

  If you possess more than your daily bag limit while on water, you must
  abide by on‑water possession limits and demonstrate you have fished
  for more than one day.
  ```
- **Correct Answer**: State each region’s daily bag limit and note that documents don’t specify a combined rule for fishing both regions on the **same day**; advise checking full regulations.

**System Response**
> Hey there! 🎣 That's a great question about rock lobster limits in Tasmania!  
>
> Based on the provided information, here's what we know about the individual daily bag limits for Rock Lobster (Eastern species):  
>
> * **Eastern Region Bag Limit:** 2 rock lobsters per day 📍  
> * **Western Region Bag Limit:** 5 rock lobsters per day 📍  
>
> *(Source: `tas_fishing_guide/species`)*  
>
> However, the provided context **does not specify** a combined rock lobster limit or a rule for how these bag limits apply if you fish in both the Eastern and Western zones *in one day*. The limits are stated separately for each region.  
>
> For the most accurate and up-to-date information on combining bag limits when fishing across different zones on the same day, I'd recommend checking the full Tasmanian recreational fishing regulations or contacting the local fisheries authority directly. ✅

**System Verification (Observed)**
- Router → RAG ✅  
- Retrieved zone‑specific rules ✅  
- Interpreted appropriately and explained limitations ✅

**Status**: ✅ **PASSED**

---

## Difficult Tests Summary

| Test ID | Failure Type | Expected Behavior | Actual Behavior | Status |
|---|---|---|---|---|
| D1 | Out of Scope | Recognise info unavailable | Correctly identified | ✅ Pass |
| D2 | Complex Regulation | May struggle | Retrieved and synthesised correctly | ✅ Pass |

**Key Finding**: Error‑handling and complex reasoning are **strong**.

---

## Summary

### Overall Performance
- **Baseline Questions**: 8/8 (100%) – all passed
- **Difficult Questions**: 2/2 (100%) – handled appropriately

### System Strengths
1. **Tool Calling**: Correct routing, parameter extraction, and consistent outputs across P4–P5, P7–P8.
2. **Error Handling**: Clear communication of limitations for out‑of‑scope queries; no crashes.
3. **Complex Reasoning**: Integrates multiple chunks and interprets regulations reliably.

### System Weaknesses
1. **Semantic Search Precision**: Occasional misses on hyper‑specific locale snippets; consider query expansion/hybrid search.
2. **Source Selection**: Sometimes cites backup/secondary sources instead of primary; improve re‑ranking.
3. **Tool Coverage**: Legal‑size helper covers a limited species set; expand for common species (e.g., bream, additional flathead variants).

### Recommendations
- **Retrieval**: Add keyword+semantic hybrid, increase top‑k, and tune chunk size/overlap.
- **Citations**: Re‑rank to prioritise canonical sources; allow the LLM to pick best among increased top‑k.
- **Tools**: Extend legal‑size coverage; add fallback to RAG when unsupported.

---

## Evaluation Methodology

### Manual Verification Process
1. **Citation Verification**: Locate the exact source text; record excerpt and confirm presence in retrieved chunks.
2. **Tool Verification**: Validate parameter extraction and compare outputs against independent expectations.
3. **Answer Verification**: Check factual accuracy, citation presence, and completeness.

### Test Execution
- **Environment**: Windows 10, Python 3.10  
- **LLM**: Gemini (gemini-2.5-flash), Temperature 0.3  
- **Vector DB**: ChromaDB (in‑memory)  
- **Embedding Model**: `all‑MiniLM‑L6‑v2`  
- **Top‑K Retrieval**: 3 chunks

---

## Files Used
- Evaluation script: `evaluation.py`
- Ground truth documents (in `data/`):
  - `tas_fishing_guide.json`


---

