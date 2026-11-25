BTW bonus 3: special characters inside a YARN
BTW project spec PDF p.4, Extra Credit: "Special characters in a YARN (:>, :), etc)"
BTW :) new line, :> tab, :: colon, :(hex) a character by its code
BTW a colon before a quote stays text, so "x:" still closes (tests/05_bool.lol needs this)
HAI
    VISIBLE "line one:)line two"         BTW two lines
    VISIBLE "name:>value"                BTW name, a tab, value
    VISIBLE "a::b"                       BTW a:b
    VISIBLE "cat :(1F431)"               BTW cat and a cat emoji
    VISIBLE "x:" + WIN                   BTW x:WIN
    VISIBLE "Value 1: "                  BTW Value 1: (an unknown colon stays as typed)
    VISIBLE SMOOSH "top" AN ":)" AN "bottom"    BTW top and bottom on two lines
KTHXBYE
