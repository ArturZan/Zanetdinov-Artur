|Case|n|m|Seed/generator|Algorithm|Run 1 (us/call)|Run 2|Run 3|Median|Correct outputs checked|
|---|---:|---:|---|---|---:|---:|---:|---:|---|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|naive|35.9|9.1|9.0|9.1|yes, = reference (1 starts)|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|22.7|6.9|20.5|20.5|yes, = reference (1 starts)|
|random|500|10|Random(4742), alphabet abcd, pattern = text[n/3, n/3+m)|rk|10.4|23.6|10.1|10.4|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|naive|7.0|4.9|3.9|4.9|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|59.1|53.3|51.7|53.3|yes, = reference (1 starts)|
|random|1500|30|Random(5742), alphabet abcd, pattern = text[n/3, n/3+m)|rk|61.5|52.3|29.5|52.3|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|naive|11.3|11.2|12.5|11.3|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|kmp|10.0|7.4|7.2|7.4|yes, = reference (1 starts)|
|random|3000|100|Random(7242), alphabet abcd, pattern = text[n/3, n/3+m)|rk|36.9|35.0|35.0|35.0|yes, = reference (1 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|naive|3.6|5.7|3.3|3.6|yes, = reference (0 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|kmp|2.1|2.2|2.2|2.2|yes, = reference (0 starts)|
|repetitive|500|10|text a^n, pattern a^(m-1)b|rk|6.2|6.3|6.2|6.2|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|naive|86.7|78.5|76.8|78.5|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|kmp|7.7|7.1|7.3|7.3|yes, = reference (0 starts)|
|repetitive|1500|30|text a^n, pattern a^(m-1)b|rk|20.6|21.1|20.7|20.7|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|naive|566.8|479.9|495.3|495.3|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|kmp|19.8|19.8|23.5|19.8|yes, = reference (0 starts)|
|repetitive|3000|100|text a^n, pattern a^(m-1)b|rk|55.7|47.2|43.3|47.2|yes, = reference (0 starts)|
