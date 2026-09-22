"""Digital job checklists.

The business plan specifies a 37-point residential checklist, a 28-point
vacation-rental turnover checklist, and a medical checklist aligned to CDC
surface-disinfection guidance. Crews tick these off in the phone app; the
counts below are asserted in the self-test at the bottom of this file.
"""

RESIDENTIAL = [
    ("Kitchen", "Counters and backsplash wiped and disinfected"),
    ("Kitchen", "Sink scrubbed, drain cleared, fixtures polished"),
    ("Kitchen", "Stovetop degreased, grates and drip pans cleaned"),
    ("Kitchen", "Microwave cleaned inside and out"),
    ("Kitchen", "Appliance exteriors wiped, fingerprints removed"),
    ("Kitchen", "Cabinet fronts and handles spot-cleaned"),
    ("Kitchen", "Trash emptied, bin wiped, fresh liner"),
    ("Kitchen", "Floor vacuumed and mopped to the edges"),
    ("Bathrooms", "Toilet cleaned and disinfected, base and behind included"),
    ("Bathrooms", "Shower and tub scrubbed, soap scum removed"),
    ("Bathrooms", "Glass doors and tile descaled"),
    ("Bathrooms", "Sink, vanity and fixtures polished"),
    ("Bathrooms", "Mirrors streak-free"),
    ("Bathrooms", "Towels straightened or replaced"),
    ("Bathrooms", "Trash emptied and relined"),
    ("Bathrooms", "Floor vacuumed and mopped, behind the toilet included"),
    ("Bedrooms", "Beds made or linens changed as instructed"),
    ("Bedrooms", "Nightstands and dressers dusted"),
    ("Bedrooms", "Mirrors and glass wiped"),
    ("Bedrooms", "Under-bed floor vacuumed where accessible"),
    ("Bedrooms", "Closet floors tidied and vacuumed"),
    ("Living areas", "All reachable surfaces dusted"),
    ("Living areas", "Electronics and screens dusted with dry microfiber"),
    ("Living areas", "Upholstery vacuumed, cushions straightened"),
    ("Living areas", "Under and behind moveable furniture vacuumed"),
    ("Living areas", "Glass tables and decor wiped"),
    ("Whole home", "Window sills and tracks wiped"),
    ("Whole home", "Baseboards checked and spot-wiped"),
    ("Whole home", "Light switches and door handles disinfected"),
    ("Whole home", "Door frames and doors spot-cleaned"),
    ("Whole home", "Ceiling fans and light fixtures dusted"),
    ("Whole home", "Air vents and returns dusted"),
    ("Whole home", "Cobwebs removed from corners and ceilings"),
    ("Whole home", "All hard floors vacuumed and mopped"),
    ("Whole home", "All carpets and rugs vacuumed"),
    ("Finish", "Before/after photos captured and uploaded"),
    ("Finish", "Final walkthrough, lights off, doors secured per access notes"),
]

VACATION_RENTAL = [
    ("Turnover", "Previous guest belongings collected, logged and photographed"),
    ("Turnover", "Damage and maintenance issues photographed and reported"),
    ("Turnover", "All trash and recycling removed from property"),
    ("Linens", "All beds stripped"),
    ("Linens", "Mattress protectors checked for stains"),
    ("Linens", "Fresh linens installed, hospital corners"),
    ("Linens", "Decorative pillows and throws re-set"),
    ("Linens", "Bath towels, hand towels and mats replaced"),
    ("Linens", "Used linens bagged for laundry"),
    ("Kitchen", "Dishwasher emptied, dishes put away"),
    ("Kitchen", "Refrigerator emptied of guest food and wiped"),
    ("Kitchen", "Counters, sink and stovetop cleaned"),
    ("Kitchen", "Coffee maker cleaned and restocked"),
    ("Kitchen", "Inventory checked against par list"),
    ("Bathrooms", "Toilets, showers and sinks cleaned and disinfected"),
    ("Bathrooms", "Mirrors and glass streak-free"),
    ("Bathrooms", "Toilet paper, soap and amenities restocked to par"),
    ("Bathrooms", "Hair removed from drains and floors"),
    ("Living areas", "All surfaces dusted and wiped"),
    ("Living areas", "Upholstery and cushions reset"),
    ("Living areas", "Remotes, switches and handles disinfected"),
    ("Living areas", "Floors vacuumed and mopped throughout"),
    ("Outdoor", "Lanai, patio or balcony swept and furniture wiped"),
    ("Outdoor", "Sand and beach gear cleared from entry"),
    ("Reset", "Thermostat set to host's turnover setting"),
    ("Reset", "Welcome materials and guest book reset"),
    ("Reset", "Photo verification of every room captured"),
    ("Reset", "Doors locked, lockbox code reset, host notified"),
]

MEDICAL = [
    ("Reception", "Check-in counters and glass disinfected"),
    ("Reception", "Waiting-room seating disinfected, arms and backs included"),
    ("Reception", "High-touch surfaces: door handles, kiosks, pens, clipboards"),
    ("Reception", "Floors vacuumed and mopped with hospital-grade solution"),
    ("Exam rooms", "Exam tables and stools disinfected with EPA List N product"),
    ("Exam rooms", "Counters, cabinets and sinks disinfected"),
    ("Exam rooms", "Dwell time observed per product label before wiping"),
    ("Exam rooms", "Regulated waste containers checked, not handled"),
    ("Exam rooms", "Floors mopped, fresh solution per room"),
    ("Restrooms", "Toilets, sinks and fixtures disinfected"),
    ("Restrooms", "Consumables restocked: soap, towels, tissue, liners"),
    ("Restrooms", "Touch points disinfected: handles, dispensers, switches"),
    ("Restrooms", "Floors disinfected, corners and behind fixtures included"),
    ("Break & admin", "Breakroom counters, sink and appliances cleaned"),
    ("Break & admin", "Workstations wiped without disturbing documents"),
    ("Break & admin", "Trash and recycling removed to dumpster"),
    ("Compliance", "Color-coded microfiber used, red reserved for restrooms"),
    ("Compliance", "Bloodborne-pathogen PPE worn where required"),
    ("Compliance", "No handling of sharps or biohazard containers"),
    ("Compliance", "Nightly log signed and alarm set on exit"),
]

MOVE_OUT = [
    ("Kitchen", "Inside all cabinets and drawers"),
    ("Kitchen", "Inside oven, broiler and racks"),
    ("Kitchen", "Inside and behind refrigerator"),
    ("Kitchen", "Inside dishwasher and filter"),
    ("Kitchen", "Counters, sink and backsplash detailed"),
    ("Bathrooms", "Inside vanities and medicine cabinets"),
    ("Bathrooms", "Tub, shower and grout scrubbed"),
    ("Bathrooms", "Toilets detailed, base and bolts included"),
    ("Whole home", "Inside all closets and shelving"),
    ("Whole home", "Interior windows, tracks and sills"),
    ("Whole home", "Baseboards, door frames and doors washed"),
    ("Whole home", "Wall scuffs and marks spot-cleaned"),
    ("Whole home", "Light fixtures, fans and vents cleaned"),
    ("Whole home", "Switch plates and outlet covers wiped"),
    ("Whole home", "All floors vacuumed, mopped and finished"),
    ("Exterior", "Garage swept out"),
    ("Exterior", "Entry, patio and lanai swept"),
    ("Finish", "Before/after photos captured for the client record"),
    ("Finish", "Final walkthrough with move-out standard checklist signed off"),
]

CONSTRUCTION = [
    ("Pass 1", "Debris and packaging removed from all rooms"),
    ("Pass 1", "Ceilings, corners and high surfaces dusted down"),
    ("Pass 1", "Vents and registers vacuumed with HEPA units"),
    ("Pass 2", "Walls wiped, drywall dust removed"),
    ("Pass 2", "Paint, adhesive, stickers and caulk residue removed"),
    ("Pass 2", "Cabinets cleaned inside and out"),
    ("Pass 2", "Windows, tracks and frames detailed"),
    ("Pass 3", "Fixtures, hardware and appliances polished"),
    ("Pass 3", "Bathrooms fully detailed and disinfected"),
    ("Pass 3", "Final HEPA vacuum of all surfaces and floors"),
    ("Pass 3", "Hard floors scrubbed and finished"),
    ("Finish", "Fine-dust check under raking light"),
    ("Finish", "Before/after photos captured and uploaded"),
    ("Finish", "Walkthrough with contractor or owner"),
]

BY_SERVICE = {
    "residential": RESIDENTIAL,
    "deep": RESIDENTIAL,
    "move": MOVE_OUT,
    "str": VACATION_RENTAL,
    "commercial": MEDICAL,
    "construction": CONSTRUCTION,
}


def for_service(service_id):
    return BY_SERVICE.get(service_id, RESIDENTIAL)


if __name__ == "__main__":
    assert len(RESIDENTIAL) == 37, len(RESIDENTIAL)
    assert len(VACATION_RENTAL) == 28, len(VACATION_RENTAL)
    print("checklists OK — residential %d, STR %d, medical %d, move-out %d, post-construction %d"
          % (len(RESIDENTIAL), len(VACATION_RENTAL), len(MEDICAL), len(MOVE_OUT), len(CONSTRUCTION)))
