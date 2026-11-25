BTW fix 1: a NUMBAR prints its first two decimals, cut and not rounded
BTW spec PDF p.6: "Casting NUMBARs to YARN will truncate the decimal portion up to two decimal places."
HAI
    WAZZUP
        I HAS A price ITZ 0.29
        I HAS A almost ITZ 3.999
    BUHBYE

    VISIBLE price                    BTW 0.29 (was 0.28)
    VISIBLE 0.57                     BTW 0.57 (was 0.56)
    VISIBLE DIFF OF 4 AN 3.14        BTW 0.86 (spec example, was 0.85)
    VISIBLE almost                   BTW 3.99, cut and not rounded
    VISIBLE MAEK 1.1 A YARN          BTW 1.10
    VISIBLE -0.001                   BTW 0.00
KTHXBYE
