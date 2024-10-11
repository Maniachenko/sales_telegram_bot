import re

# # Define the shop_data dictionary with the examples provided
# shop_data = {
#     "EsoMarket": {
#         "item_price": ["2190"]  # Expected output: 21.9
#     },
#     "Penny": {
#         "item_price": [
#             "14 90 22.90", "13 90 1990", "69 06", "39.90", "47 57.90", "4990",
#             "19 2790", "69 11680", "9 90", "26 90 * * 4290", "199.",
#             "19 90 25.90 2", "4", "CENA BE Z PENNY KART Y 8490",
#             "59.90", "x 100 24 90 34.90"
#         ],
#         "item_member_price": [
#             "79,00", "129,\"*", "MOJ E PENNY KARTA 49 90",
#             "MOJ E PENNY KARTA 24 90", "MOJE PENNY KARTA 79 90"
#         ],
#         "item_initial_price": [
#             "159,90K", "359,90K", "CENA BEZ PENNY KART Y 5490", "CENA BEZ PENNY KART Y 29.90"
#         ]
#     },
#     "Billa": {
#         "item_price": [
#             "6990", "9990 12990", "27 2780", "2290 PRIKOUPI 1ks", "890 1090", "1",
#             "bèzná cena 5990", "2995 K UP TE 2", "2690 EN AZA 1 KS"
#         ],
#         "item_initial_price": [
#             "bèzná cena 6390", "bèznacena6990", "bèzná cena5350"
#         ],
#         "item_member_price": [
#             "2390", "75bodi", "21.90"
#         ]
#     },
#     "Albert Hypermarket": {
#         "item_price": [
#             "369.-", "990", "6", "BE Z 5990 A PLI K ACE", "10990", "22 30", "31'90",
#             "BE Z 499- A PLI K ACE", "BE Z 066", "1190 BE Z A PLI K ACE", "BE Z 179: A PLI K ACE"
#         ],
#         "item_initial_price": [
#             "BE ZN A CENA 499.", "BE ZN A CENA 116.80", "BE ZN A CENA 179:",
#             "BE ZN A CENA 149.90", "BE ZN A CENA 890-"
#         ],
#         "item_member_price": [
#             "5490", "21 90", "449.-"
#         ]
#     },
#     "Tesco Supermarket": {
#         "item_member_price": [
#             "6990 Club card cena", "2690 Club card con a", "12.7. - 14.7.  9890 Club card cena"
#         ],
#         "item_initial_price": [
#             "78,90 cena", "Boz nd 49,90 cena", "Bo in a 21,90 cena",
#             "Bozna 99,90 cena", "179,90", "Beina 45,90 cena", "Boina 49,90 cena"
#         ],
#         "item_price": [
#             "-30%", "-34%", "-30%", "HOP!"
#         ]
#     },
#     "Albert Supermarket": {
#         "item_price": [
#             "4990", "22'90", "289.-", "BE Z 2190 A PLI K ACE", "19 90",
#             "32%", "CIA", "BEZ 9990 APLIKACE", "BE Z 389- A PLI K ACE"
#         ],
#         "item_initial_price": [
#             "BE ZN A CENA 77.90", "BE ZN A CENA 179:", "BE ZN A CENA 329-", "BE ZN A CENA 699."
#         ],
#         "item_member_price": [
#             "5390", "12 90", "349.-"
#         ]
#     },
#     "Lidl": {
#         "item_price": [
#             "349.90", "184.-", "59999.", "94.0"
#         ],
#         "item_member_price": [
#             "27.90"
#         ]
#     },
#     "Ratio": {
#         "item_price": [
#             "21,34 be zD PH 23,90 vc et neD PH", "362,81bezDPH 439,00 vcetneDPH"
#         ]
#     },
#     "Kaufland": {
#         "item_price": [
#             "15,90", "od 49,90", "1 49,90 119,90 169,90", "129,90 149,90 179,90 249,90 349,90",
#             "pouze 69.90", "2499.-", "nezavisladoporucena spotrebitelskacena 2699, 1899,-", "1599,-"
#         ],
#         "item_member_price": [
#             "199,90", "349,-", "149,90"
#         ]
#     },
#     "Tesco Hypermarket": {
#         "item_member_price": [
#             "1990 Club card cena", "1790 Club card con a"
#         ],
#         "item_initial_price": [
#             "28,90 cena", "Bo ena 89,90 cena", "Bo in a 114,90 cena", "59,90",
#             "been 96,90 cena", "Boz na 44,90 cena", "Boz nd 33,90 cena",
#             "Beina 329,90 cena", "Boina 99,90 cena", "Bozna 189,90 cena",
#             "802n496,90", "Be in a 239,90 cena", "2499,00 cena"
#         ],
#         "item_price": [
#             "1390 Club card cena", "NYNI", "-48%", "-30%", "NYNI"
#         ]
#     },
#     "Tamda Foods": {
#         "item_member_price": [
#             "1290 KC", "3490Kc", "4990K", "5290KC", "50%KC"
#         ],
#         "item_price": [
#             "("
#         ]
#     },
#     "Globus": {
#         "item_price": [
#             "3990", "24,90", "139,-", "14'90", "17 90", "V/VHODNEI"
#         ],
#         "item_member_price": [
#             "9990", "62%", "44'90"
#         ]
#     },
#     "Bene": {
#         "item_price": [
#             "24900", "99°"
#         ]
#     },
#     "CBA Potraviny": {
#         "item_price": [
#             "3190", "24'90"
#         ]
#     },
#     "Flop": {
#         "item_price": [
#             "2290"
#         ]
#     },
#     "Flop Top": {
#         "item_price": [
#             "13990", "od 1990", "od2990", "19.90K", "od 390", "99.90Kc"
#         ],
#         "item_member_price": [
#             "7990"
#         ]
#     },
#     "Travel Free": {
#         "item_price": [
#             "4.99", "€7.99\n€5.69"
#         ],
#         "item_member_price": [
#             "CLUB PREIS 15.99"
#         ]
#     },
#     "CBA Premium": {
#         "item_price": [
#             "2390", "20'90"
#         ]
#     },
#     "Lidl Shop": {
#         "item_price": [
#             "59999.", "399.90"
#         ]
#     },
#     "CBA Market": {
#         "item_price": [
#             "5790"
#         ]
#     }
# }

shop_data = {
    "EsoMarket": {
        "item_price": [
            {"input_ocr_string": "2190", "necessary_output": {"item_price": 21.9}}
        ]
    },
    "Penny": {
        "item_price": [
            {"input_ocr_string": "14 90 22.90", "necessary_output": {"item_price": 14.9, "initial_price": 22.9}},
            {"input_ocr_string": "13 90 1990", "necessary_output": {"item_price": 13.9, "initial_price": 19.9}},
            {"input_ocr_string": "69 06", "necessary_output": {"item_price": 69.06}},
            {"input_ocr_string": "39.90", "necessary_output": {"item_price": 39.9}},
            {"input_ocr_string": "47 57.90", "necessary_output": {"item_price": 47, "initial_price": 57.9}},
            {"input_ocr_string": "4990", "necessary_output": {"item_price": 49.9}},
            {"input_ocr_string": "19 2790", "necessary_output": {"item_price": 19, "initial_price": 27.9}},
            {"input_ocr_string": "69 11680", "necessary_output": {"item_price": 69, "initial_price": 116.8}},
            {"input_ocr_string": "9 90", "necessary_output": {"item_price": 9.9}},
            {"input_ocr_string": "26 90 * * 4290", "necessary_output": {"item_price": 26.9, "initial_price": 42.9}},
            {"input_ocr_string": "199.", "necessary_output": {"item_price": 199.0}},
            {"input_ocr_string": "19 90 25.90 2", "necessary_output": {"item_price": 19.9, "initial_price": 25.9}},
            {"input_ocr_string": "4", "necessary_output": {"item_price": 4.0}},
            {"input_ocr_string": "CENA BE Z PENNY KART Y 8490", "necessary_output": {"item_price": 84.9}},
            {"input_ocr_string": "59.90", "necessary_output": {"item_price": 59.9}},
            {"input_ocr_string": "x 100 24 90 34.90", "necessary_output": {"item_price": 24.9, "initial_price": 34.9}},
        ],
        "item_member_price": [
            {"input_ocr_string": "79,00", "necessary_output": {"item_member_price": 79.0}},
            {"input_ocr_string": "129,\"*", "necessary_output": {"item_member_price": 129.0}},
            {"input_ocr_string": "MOJ E PENNY KARTA 49 90", "necessary_output": {"item_member_price": 49.9}},
            {"input_ocr_string": "MOJ E PENNY KARTA 24 90", "necessary_output": {"item_member_price": 24.9}},
            {"input_ocr_string": "MOJE PENNY KARTA 79 90", "necessary_output": {"item_member_price": 79.9}},
        ],
        "item_initial_price": [
            {"input_ocr_string": "159,90K", "necessary_output": {"item_initial_price": 159.9}},
            {"input_ocr_string": "359,90K", "necessary_output": {"item_initial_price": 359.9}},
            {"input_ocr_string": "CENA BEZ PENNY KART Y 5490", "necessary_output": {"item_initial_price": 54.9}},
            {"input_ocr_string": "CENA BEZ PENNY KART Y 29.90", "necessary_output": {"item_initial_price": 29.9}},
        ]
    },
    "Billa": {
        "item_price": [
            {"input_ocr_string": "6990", "necessary_output": {"item_price": 69.9}},
            {"input_ocr_string": "9990 12990", "necessary_output": {"item_price": 99.9, "initial_price": 129.9}},
            {"input_ocr_string": "27 2780", "necessary_output": {"item_price": 27.0, "initial_price": 27.8}},
            {"input_ocr_string": "2290 PRIKOUPI 1ks", "necessary_output": {"item_price": 22.9}},
            {"input_ocr_string": "890 1090", "necessary_output": {"item_price": 8.9, "initial_price": 10.9}},
            {"input_ocr_string": "1", "necessary_output": {"item_price": 1.0}},
            {"input_ocr_string": "bèzná cena 5990", "necessary_output": {"item_price": 59.9}},
            {"input_ocr_string": "2995 K UP TE 2", "necessary_output": {"item_price": 29.95}},
            {"input_ocr_string": "2690 EN AZA 1 KS", "necessary_output": {"item_price": 26.9}},
        ],
        "item_initial_price": [
            {"input_ocr_string": "bèzná cena 6390", "necessary_output": {"item_initial_price": 63.9}},
            {"input_ocr_string": "bèznacena6990", "necessary_output": {"item_initial_price": 69.9}},
            {"input_ocr_string": "bèzná cena5350", "necessary_output": {"item_initial_price": 53.5}},
        ],
        "item_member_price": [
            {"input_ocr_string": "2390", "necessary_output": {"item_member_price": 23.9}},
            {"input_ocr_string": "75bodi", "necessary_output": {"item_member_price": "75bodi"}},
            {"input_ocr_string": "21.90", "necessary_output": {"item_member_price": 21.9}},
        ]
    },
    "Albert Hypermarket": {
        "item_price": [
            {"input_ocr_string": "369.-", "necessary_output": {"item_price": 369.0}},
            {"input_ocr_string": "990", "necessary_output": {"item_price": 9.9}},
            {"input_ocr_string": "6", "necessary_output": {"item_price": 6.0}},
            {"input_ocr_string": "BE Z 5990 A PLI K ACE", "necessary_output": {"item_price": 59.9}},
            {"input_ocr_string": "10990", "necessary_output": {"item_price": 109.9}},
            {"input_ocr_string": "22 30", "necessary_output": {"item_price": 22.3}},
            {"input_ocr_string": "31'90", "necessary_output": {"item_price": 31.9}},
            {"input_ocr_string": "BE Z 499- A PLI K ACE", "necessary_output": {"item_price": 499.0}},
            {"input_ocr_string": "BE Z 066", "necessary_output": {"item_price": 66.0}},
            {"input_ocr_string": "1190 BE Z A PLI K ACE", "necessary_output": {"item_price": 11.9}},
            {"input_ocr_string": "BE Z 179: A PLI K ACE", "necessary_output": {"item_price": 179.0}},
        ],
        "item_initial_price": [
            {"input_ocr_string": "BE ZN A CENA 499.", "necessary_output": {"item_initial_price": 499.0}},
            {"input_ocr_string": "BE ZN A CENA 116.80", "necessary_output": {"item_initial_price": 116.8}},
            {"input_ocr_string": "BE ZN A CENA 179:", "necessary_output": {"item_initial_price": 179.0}},
            {"input_ocr_string": "BE ZN A CENA 149.90", "necessary_output": {"item_initial_price": 149.9}},
            {"input_ocr_string": "BE ZN A CENA 890-", "necessary_output": {"item_initial_price": 890.0}},
        ],
        "item_member_price": [
            {"input_ocr_string": "5490", "necessary_output": {"item_member_price": 54.9}},
            {"input_ocr_string": "21 90", "necessary_output": {"item_member_price": 21.9}},
            {"input_ocr_string": "449.-", "necessary_output": {"item_member_price": 449.0}},
        ]
    },
    "Tesco Supermarket": {
        "item_member_price": [
            {"input_ocr_string": "6990 Club card cena", "necessary_output": {"item_member_price": 69.9}},
            {"input_ocr_string": "2690 Club card con a", "necessary_output": {"item_member_price": 26.9}},
            {"input_ocr_string": "12.7. - 14.7.  9890 Club card cena", "necessary_output": {"item_member_price": 98.9}},
        ],
        "item_initial_price": [
            {"input_ocr_string": "78,90 cena", "necessary_output": {"item_initial_price": 78.9}},
            {"input_ocr_string": "Boz nd 49,90 cena", "necessary_output": {"item_initial_price": 49.9}},
            {"input_ocr_string": "Bo in a 21,90 cena", "necessary_output": {"item_initial_price": 21.9}},
            {"input_ocr_string": "Bozna 99,90 cena", "necessary_output": {"item_initial_price": 99.9}},
            {"input_ocr_string": "179,90", "necessary_output": {"item_initial_price": 179.9}},
            {"input_ocr_string": "Beina 45,90 cena", "necessary_output": {"item_initial_price": 45.9}},
            {"input_ocr_string": "Boina 49,90 cena", "necessary_output": {"item_initial_price": 49.9}},
        ],
        "item_price": [
            {"input_ocr_string": "-30%", "necessary_output": None},
            {"input_ocr_string": "-34%", "necessary_output": None},
            {"input_ocr_string": "-30%", "necessary_output": None},
            {"input_ocr_string": "HOP!", "necessary_output": None}
        ]
    },
    "Lidl": {
        "item_price": [
            {"input_ocr_string": "349.90", "necessary_output": {"item_price": 349.9}},
            {"input_ocr_string": "184.-", "necessary_output": {"item_price": 184.0}},
            {"input_ocr_string": "59999.", "necessary_output": {"item_price": 59999.0}},
            {"input_ocr_string": "94.0", "necessary_output": {"item_price": 94.0}},
        ],
        "item_member_price": [
            {"input_ocr_string": "27.90", "necessary_output": {"item_member_price": 27.9}},
        ]
    },
    "Kaufland": {
        "item_price": [
            {"input_ocr_string": "15,90", "necessary_output": {"item_price": 15.9}},
            {"input_ocr_string": "od 49,90", "necessary_output": {"item_price": 49.9}},
            {"input_ocr_string": "1 49,90 119,90 169,90", "necessary_output": None},  # No output, irrelevant sequence
            {"input_ocr_string": "129,90 149,90 179,90 249,90 349,90", "necessary_output": None},
            # No output, multiple prices
            {"input_ocr_string": "pouze 69.90", "necessary_output": {"item_price": 69.9}},
            {"input_ocr_string": "2499.-", "necessary_output": {"item_price": 2499.0}},
            {"input_ocr_string": "nezavisladoporucena spotrebitelskacena 2699, 1899,-",
             "necessary_output": {"item_price": 1899.0, "initial_price": 2699.0}},
            {"input_ocr_string": "1599,-", "necessary_output": {"item_price": 1599.0}},
        ],
        "item_member_price": [
            {"input_ocr_string": "199,90", "necessary_output": {"item_member_price": 199.9}},
            {"input_ocr_string": "349,-", "necessary_output": {"item_member_price": 349.0}},
            {"input_ocr_string": "149,90", "necessary_output": {"item_member_price": 149.9}},
        ]
    },
    "Flop Top": {
        "item_price": [
            {"input_ocr_string": "13990", "necessary_output": {"item_price": 139.9}},
            {"input_ocr_string": "od 1990", "necessary_output": {"item_price": 19.9}},
            {"input_ocr_string": "od2990", "necessary_output": {"item_price": 29.9}},
            {"input_ocr_string": "19.90K", "necessary_output": {"item_price": 19.9}},
            {"input_ocr_string": "od 390", "necessary_output": {"item_price": 3.9}},
            {"input_ocr_string": "99.90Kc", "necessary_output": {"item_price": 99.9}},
        ],
        "item_member_price": [
            {"input_ocr_string": "7990", "necessary_output": {"item_member_price": 79.9}},
        ]
    },
    "Travel Free": {
        "item_price": [
            {"input_ocr_string": "4.99", "necessary_output": {"item_price": 4.99}},
            {"input_ocr_string": "€7.99\n€5.69", "necessary_output": {"item_price": 7.99, "initial_price": 5.69}},
        ],
        "item_member_price": [
            {"input_ocr_string": "CLUB PREIS 15.99", "necessary_output": {"item_member_price": 15.99}},
        ]
    },
    "CBA Potraviny": {
        "item_price": [
            {"input_ocr_string": "3190", "necessary_output": {"item_price": 31.9}},
            {"input_ocr_string": "24'90", "necessary_output": {"item_price": 24.9}},
        ]
    },
    "Bene": {
        "item_price": [
            {"input_ocr_string": "24900", "necessary_output": {"item_price": 249.0}},
            {"input_ocr_string": "99°", "necessary_output": {"item_price": 99.0}},
        ]
    },
    "CBA Premium": {
        "item_price": [
            {"input_ocr_string": "2390", "necessary_output": {"item_price": 23.9}},
            {"input_ocr_string": "20'90", "necessary_output": {"item_price": 20.9}},
        ]
    },
    "Lidl Shop": {
        "item_price": [
            {"input_ocr_string": "59999.", "necessary_output": {"item_price": 59999.0}},
            {"input_ocr_string": "399.90", "necessary_output": {"item_price": 399.9}},
        ]
    },
    "CBA Market": {
        "item_price": [
            {"input_ocr_string": "5790", "necessary_output": {"item_price": 57.9}},
        ]
    },

    "Makro": {
        "item_price": [
            {"input_ocr_string": "10,90 12,21*", "necessary_output": {"item_price": 10.9, "initial_price": 12.21}},
            {"input_ocr_string": "1-2 BAL 59,90 67,09*",
             "necessary_output": {"item_price": 59.9, "initial_price": 67.09, "packaging": "1-2 BAL"}},
            {"input_ocr_string": "39,80 44,58*", "necessary_output": {"item_price": 39.8, "initial_price": 44.58}},
            {"input_ocr_string": "12500 151,25*", "necessary_output": {"item_price": 125.0, "initial_price": 151.25}},
            {"input_ocr_string": "3 BAL. A VICE 52,90 59,25*",
             "necessary_output": {"item_price": 52.9, "initial_price": 59.25, "packaging": "3 BAL. A VICE"}},
            {"input_ocr_string": "1 BAL 49,90", "necessary_output": {"item_price": 49.9, "packaging": "1 BAL"}},
            {"input_ocr_string": "5 ksAViCE 97,00 108,64",
             "necessary_output": {"item_price": 97.0, "initial_price": 108.64, "packaging": "5 ksAViCE"}},
            {"input_ocr_string": "10 ksA ViCE 59,90 67,09*",
             "necessary_output": {"item_price": 59.9, "initial_price": 67.09, "packaging": "10 ksA ViCE"}},
            {"input_ocr_string": "3-7 BAL 1950 21,84*",
             "necessary_output": {"item_price": 19.5, "initial_price": 21.84, "packaging": "3-7 BAL"}},
            {"input_ocr_string": "45,90 51,41*", "necessary_output": {"item_price": 45.9, "initial_price": 51.41}},
            {"input_ocr_string": "5 ksAViCE 4490 50,29*",
             "necessary_output": {"item_price": 44.9, "initial_price": 50.29, "packaging": "5 ksAViCE"}}
        ],
        "item_member_price": [
            {"input_ocr_string": "MRA ZE NE", "necessary_output": None},
            {"input_ocr_string": "10000bodu", "necessary_output": {"item_member_price": "10000bodu"}},
            {"input_ocr_string": "CER STVE CH LA ZEN E", "necessary_output": None}
        ],
        "item_initial_price": [
            {"input_ocr_string": "159,00 178,08*",
             "necessary_output": {"item_initial_price": 178.08, "item_price": 159.0}},
            {"input_ocr_string": "1250 15,13*", "necessary_output": {"item_initial_price": 15.13, "item_price": 12.5}},
            {"input_ocr_string": "24500 27,44*",
             "necessary_output": {"item_initial_price": 27.44, "item_price": 245.0}},
            {"input_ocr_string": "12,40 15,00*", "necessary_output": {"item_price": 12.4, "initial_price": 15.0}},
            {"input_ocr_string": "14500 162,29*", "necessary_output": {"item_price": 145.0, "initial_price": 162.29}}
        ]
    },
    "Ratio": {
        "item_price": [
            {"input_ocr_string": "21,34 be zD PH 23,90 vc et neD PH",
             "necessary_output": {"item_price": 21.34, "initial_price": 23.9}},
            {"input_ocr_string": "362,81bezDPH 439,00 vcetneDPH",
             "necessary_output": {"item_price": 362.81, "initial_price": 439.0}},
        ]
    },
    "Globus": {
        "item_price": [
            {"input_ocr_string": "3990", "necessary_output": {"item_price": 39.9}},
            {"input_ocr_string": "24,90", "necessary_output": {"item_price": 24.9}},
            {"input_ocr_string": "139,-", "necessary_output": {"item_price": 139.0}},
            {"input_ocr_string": "14'90", "necessary_output": {"item_price": 14.9}},
            {"input_ocr_string": "17 90", "necessary_output": {"item_price": 17.9}},
            {"input_ocr_string": "V/VHODNEI", "necessary_output": None}  # No price, invalid string
        ],
        "item_member_price": [
            {"input_ocr_string": "9990", "necessary_output": {"item_member_price": 99.9}},
            {"input_ocr_string": "62%", "necessary_output": None},  # No price, percentage discount
            {"input_ocr_string": "44'90", "necessary_output": {"item_member_price": 44.9}},
        ]
    },
    "Tamda Foods": {
        "item_member_price": [
            {"input_ocr_string": "1290 KC", "necessary_output": {"item_member_price": 12.9}},
            {"input_ocr_string": "3490Kc", "necessary_output": {"item_member_price": 34.9}},
            {"input_ocr_string": "4990K", "necessary_output": {"item_member_price": 49.9}},
            {"input_ocr_string": "5290KC", "necessary_output": {"item_member_price": 52.9}},
            {"input_ocr_string": "50%KC", "necessary_output": None},  # No price, percentage
        ],
        "item_price": [
            {"input_ocr_string": "(", "necessary_output": None},  # No price, invalid string
        ]
    }
}


# Helper function to parse price strings into floats
def parse_price(price_str):
    # Remove non-numeric characters except for decimal points or commas
    clean_str = re.sub(r'[^0-9.,]', '', price_str)
    clean_str = clean_str.replace(',', '.').replace("'", '.')

    try:
        # If it contains a decimal, treat it as a float
        if '.' in clean_str:
            return float(clean_str)
        # Otherwise, treat the last two digits as the decimal part
        elif len(clean_str) > 2:
            return float(clean_str[:-2] + '.' + clean_str[-2:])
        else:
            return float(clean_str)
    except ValueError:
        return None


# EsoMarket Condition
def process_esomarket(price_str):
    price = parse_price(price_str)
    return price if price else None


def process_penny(price_str, price_type):
    # Extract all numeric parts from the price string
    prices = re.findall(r'\d+[.,]?\d*', price_str)

    # Clean up extracted prices and convert them to floats
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # Common cents values like 90 or 99
    common_cents = [90, 99]

    # Handle cases based on the length of parsed prices
    if len(parsed_prices) == 3:
        # Handle cases like "19 90 25.90 2"
        item_price = float(f"{int(parsed_prices[0])}.{int(parsed_prices[1])}")
        initial_price = parsed_prices[2]
        return {"item_price": item_price, "initial_price": initial_price}

    if len(parsed_prices) == 2:
        # If the second price is commonly a "cents" part like 90 or 99, merge with the first
        if parsed_prices[1] in common_cents:
            return {"item_price": float(f"{int(parsed_prices[0])}.{int(parsed_prices[1])}")}
        else:
            return {"item_price": parsed_prices[0], "initial_price": parsed_prices[1]}

    if len(parsed_prices) == 1:
        return {"item_price": parsed_prices[0]}

    return None


# Billa Condition
def process_billa(price_str, price_type):
    # Detect volume keywords: pri koupi, kupte, etc.
    volume_keywords = ['pri', 'koupi', 'kupte', 'ks', 'bodi', 'bodu', 'up te', 'aza']
    volume_detected = any(keyword in price_str.lower() for keyword in volume_keywords)

    # Extract numeric parts from the string
    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # Handle specific distracted membership or volume words
    if 'bodi' in price_str.lower() or 'bodu' in price_str.lower():
        return {'item_member_price': '75bodi'}

    # Check if there are two prices and handle them
    if len(parsed_prices) == 2:
        # If the second value is an integer <5, treat it as volume, not initial_price
        if parsed_prices[1] < 5 and parsed_prices[1].is_integer():
            return {"item_price": parsed_prices[0], "volume": str(int(parsed_prices[1]))}
        else:
            return {"item_price": parsed_prices[0], "initial_price": parsed_prices[1]}
    elif len(parsed_prices) == 1:
        return {"item_price": parsed_prices[0]}

    return None


# Define Albert Hypermarket parsing method
def process_albert_hypermarket(price_str, price_type):
    # Clean string by keeping numbers and relevant separators
    clean_str = re.sub(r'[^0-9\s.,\'\-:]', '', price_str)  # Allow special chars like -, :, '

    # Handle specific cases for '-' or ':' as separators for integer prices
    combined_prices = []
    tokens = clean_str.split()

    for token in tokens:
        # Case 1: Numbers ending with "-" or ":"
        if token.endswith('-') or token.endswith(':'):
            token = token[:-1]  # Remove the trailing symbol
            combined_prices.append(parse_price(token))
        elif "'" in token:
            # Case 2: Handle cases like "31'90"
            parts = token.split("'")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                combined_price = f"{parts[0]}.{parts[1]}"
                combined_prices.append(parse_price(combined_price))
            else:
                combined_prices.append(parse_price(token))
        else:
            combined_prices.append(parse_price(token))

    # Filter out None values
    parsed_prices = [p for p in combined_prices if p is not None]

    # Condition: If the price is less than 5, treat it as invalid (exclude it)
    if parsed_prices and parsed_prices[0] < 5:
        return None

    # Assign prices based on the price_type
    if price_type == "item_member_price":
        if parsed_prices:
            return {"item_member_price": parsed_prices[0]}
    elif price_type == "item_initial_price":
        if parsed_prices:
            return {"item_initial_price": parsed_prices[0]}
    else:
        if parsed_prices:
            return {"item_price": parsed_prices[0]}

    return None


# Function to handle Tesco Supermarket OCR strings
def process_tesco_supermarket(price_str, price_type):
    # Handle dates (e.g., "12.7. - 14.7.") by ignoring them
    date_pattern = r'\d{1,2}\.\d{1,2}\.\s*-\s*\d{1,2}\.\d{1,2}\.'  # Pattern for dates like "12.7. - 14.7."
    clean_str = re.sub(date_pattern, '', price_str)

    # Skip strings with percentages or irrelevant text
    if "%" in clean_str or "HOP" in clean_str:
        return None

    # Extract price values, specifically for club card or "cena" keyword
    prices = re.findall(r'\d+[.,]?\d*', clean_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # Logic to differentiate between item prices and initial prices
    if price_type == "item_member_price":
        if parsed_prices:
            return {"item_member_price": parsed_prices[0]}
    elif price_type == "item_initial_price":
        if parsed_prices:
            return {"item_initial_price": parsed_prices[0]}
    else:
        if parsed_prices:
            return {"item_price": parsed_prices[0]}

    return None


# Lidl Condition
def process_lidl(price_str):
    return parse_price(price_str)


# Kaufland Condition
def process_kaufland(price_str, price_type):
    if re.search(r'(\d+[.,]\d+)\s+(\d+[.,]\d+)', price_str):
        return None  # Skip sequences of more than 2 prices

    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    if len(parsed_prices) == 2:
        return {"item_price": parsed_prices[-1], "initial_price": parsed_prices[0]}
    elif len(parsed_prices) == 1:
        return {"item_price": parsed_prices[0]}
    return None


# Flop Top Condition
def process_flop_top(price_str, price_type):
    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    if len(parsed_prices) == 2:
        return {"item_price": parsed_prices[0], "initial_price": parsed_prices[1]}
    elif len(parsed_prices) == 1:
        return {"item_price": parsed_prices[0]}
    return None


# Travel Free Condition
def process_travel_free(price_str, price_type):
    # Removing any € symbols to focus only on numeric data
    clean_str = price_str.replace("€", "").strip()

    # Find all the price values in the string
    prices = re.findall(r'\d+[.,]?\d*', clean_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # Ensure prices are sorted correctly (sale price is less than initial price)
    if len(parsed_prices) == 2:
        sale_price = min(parsed_prices)
        initial_price = max(parsed_prices)
        return {"item_price": sale_price, "initial_price": initial_price}

    # If we only have one price, return it as the item price
    elif len(parsed_prices) == 1:
        return {"item_price": parsed_prices[0]}

    return None


# CBA Potraviny Condition
def process_cba_potraviny(price_str):
    return parse_price(price_str)


# Bene Condition
def process_bene(price_str):
    return parse_price(price_str)


# CBA Premium Condition
def process_cba_premium(price_str):
    return parse_price(price_str)


# Lidl Shop Condition
def process_lidl_shop(price_str):
    return parse_price(price_str)


# CBA Market Condition
def process_cba_market(price_str):
    return parse_price(price_str)


# Updated Makro Condition with improved packaging detection
def process_makro(price_str, price_type):
    # Extract packaging information (must be at the beginning of the string)
    packaging_pattern = re.match(r'^(\d+-?\d?\s*(BAL|ks|A VICE|AViCE))', price_str)

    # If packaging is found, extract it and continue processing the price
    packaging = None
    if packaging_pattern:
        packaging = packaging_pattern.group()  # Extract the packaging
        price_str = price_str[len(packaging):].strip()  # Remove packaging from the price string

    # Extract all numeric parts (prices) after the packaging
    prices = re.findall(r'\d+[.,]?\d*', price_str)

    # Convert extracted prices to float
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # If there are two prices, assign them as item_price and initial_price
    if len(parsed_prices) >= 2:
        return {
            "item_price": parsed_prices[0],
            "initial_price": parsed_prices[1],
            "packaging": packaging
        }
    elif len(parsed_prices) == 1:
        # If there's only one price, treat it as the item price
        return {
            "item_price": parsed_prices[0],
            "packaging": packaging
        }
    else:
        return None


# Function to process Ratio price strings
def process_ratio(price_str):
    # Extract prices ignoring "bezDPH" or "vcetneDPH" text
    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # If two prices are found, one should be item_price, the other initial_price
    if len(parsed_prices) == 2:
        return {"cena bez dph": parsed_prices[0], "item_price": parsed_prices[1]}
    return None


# Function to process Globus price strings
def process_globus(price_str, price_type):
    # Skip percentage strings or invalid non-numeric inputs
    if "%" in price_str or re.search(r'[^\d.,\'\s-]', price_str):
        return None

    # Handle cases like "14'90" or "44'90" by replacing apostrophe with a decimal point
    price_str = price_str.replace("'", ".")

    # Handle cases like "17 90" by joining them into a valid decimal format
    if re.search(r'\d+\s+\d{2}', price_str):
        price_str = price_str.replace(" ", ".")

    # Extract all numeric parts from the price string
    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    # Handle item_price and item_member_price based on price_type
    if price_type == "item_price":
        # If one price is found, return it as the item price
        if len(parsed_prices) == 1:
            return {"item_price": parsed_prices[0]}
    elif price_type == "item_member_price":
        # If member price is found, return it
        if len(parsed_prices) == 1:
            return {"item_member_price": parsed_prices[0]}

    return None


# Function to process Tamda Foods price strings
def process_tamda_foods(price_str, price_type):
    # Skip percentage strings and invalid inputs
    if "%" in price_str or "(" in price_str:
        return None

    # Handle cases like "1290 KC", "3490Kc", and "5290KC" (ignoring the "KC" part)
    price_str = re.sub(r'[KCkc]+', '', price_str).strip()

    # Extract numeric parts
    prices = re.findall(r'\d+[.,]?\d*', price_str)
    parsed_prices = [parse_price(p) for p in prices if parse_price(p) is not None]

    if len(parsed_prices) == 1:
        if price_type == "item_member_price":
            return {"item_member_price": parsed_prices[0]}
        elif price_type == "item_price":
            return {"item_price": parsed_prices[0]}

    return None


# General handler that dispatches to the correct shop-specific function
def process_shop_data(shop_data):
    processed_data = {}

    for shop, data in shop_data.items():
        processed_shop_data = {}

        for price_type, price_list in data.items():
            processed_prices = []

            for price_str in price_list:
                # Dispatch to the correct shop function
                if shop == "EsoMarket":
                    price = process_esomarket(price_str["input_ocr_string"])
                elif shop == "Penny":
                    price = process_penny(price_str["input_ocr_string"], price_type)
                elif shop == "Billa":
                    price = process_billa(price_str["input_ocr_string"], price_type)
                elif shop == "Albert Hypermarket":
                    price = process_albert_hypermarket(price_str["input_ocr_string"], price_type)
                elif shop == "Tesco Supermarket":
                    price = process_tesco_supermarket(price_str["input_ocr_string"], price_type)
                elif shop == "Lidl":
                    price = process_lidl(price_str["input_ocr_string"])
                elif shop == "Kaufland":
                    price = process_kaufland(price_str["input_ocr_string"], price_type)
                elif shop == "Flop Top":
                    price = process_flop_top(price_str["input_ocr_string"], price_type)
                elif shop == "Travel Free":
                    price = process_travel_free(price_str["input_ocr_string"], price_type)
                elif shop == "CBA Potraviny":
                    price = process_cba_potraviny(price_str["input_ocr_string"])
                elif shop == "Bene":
                    price = process_bene(price_str["input_ocr_string"])
                elif shop == "CBA Premium":
                    price = process_cba_premium(price_str["input_ocr_string"])
                elif shop == "Lidl Shop":
                    price = process_lidl_shop(price_str["input_ocr_string"])
                elif shop == "CBA Market":
                    price = process_cba_market(price_str["input_ocr_string"])
                elif shop == "Makro":
                    price = process_makro(price_str["input_ocr_string"], price_type)
                elif shop == "Ratio":
                    price = process_ratio(price_str["input_ocr_string"])
                elif shop == "Globus":
                    price = process_globus(price_str["input_ocr_string"], price_type)
                elif shop == "Tamda Foods":
                    price = process_tamda_foods(price_str["input_ocr_string"], price_type)
                else:
                    price = None  # Add more shops as needed

                processed_prices.append({
                    "input_ocr_string": price_str["input_ocr_string"],
                    "processed_string": price,
                    "necessary_output": price_str["necessary_output"]
                })

            processed_shop_data[price_type] = processed_prices
        processed_data[shop] = processed_shop_data

    return processed_data


if __name__ == '__main__':
    # Process the entire shop data
    processed_data = process_shop_data(shop_data)

    # Debugging: Print the outputs for comparison with the expected results
    for shop, data in processed_data.items():
        print(f"\nProcessed data for {shop}:")
        for price_type, prices in data.items():
            print(f"  {price_type}:")
            for price_info in prices:
                print(f"    input_ocr_string: {price_info['input_ocr_string']}, "
                      f"processed_string: {price_info['processed_string']}, "
                      f"necessary_output: {price_info['necessary_output']}")
