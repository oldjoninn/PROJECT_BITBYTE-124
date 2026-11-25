BTW bonus 4: SMOOSH may end with an optional MKAY
BTW spec PDF p.5: "SMOOSH does not require the MKAY keyword."
HOW IZ I echo YR s
    FOUND YR s
IF U SAY SO

HAI
    VISIBLE SMOOSH "a" AN "b"                            BTW ab (no MKAY, as before)
    VISIBLE SMOOSH "a" AN "b" MKAY                       BTW ab (was a syntax error)
    VISIBLE SMOOSH "a" AN "b" MKAY + "c"                 BTW abc
    VISIBLE I IZ echo YR SMOOSH "x" AN "y" MKAY          BTW xy (the MKAY closes the call)
    VISIBLE I IZ echo YR SMOOSH "x" AN "y" MKAY MKAY     BTW xy (one for SMOOSH, one for the call)
KTHXBYE
