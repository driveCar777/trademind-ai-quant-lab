# DTE_ROLL_WINDOW_V1

Days-to-expiry and official front-contract roll. Not curve slope. Not OI. Not volume.

Near-expiry uses settlement knowledge (same session 21:00Z) because DTE is known from the definition, not from T+1 statistics. Front-roll is known when the new front is selected after that session's settlement.
