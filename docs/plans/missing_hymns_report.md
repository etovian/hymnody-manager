# Missing Discs & Hymns Audit Report (LSB 331 - 986)

**Project**: Hymnody Manager  
**Target Audio Directory**: `c:\dev\IdeaProjects\hymnody-manager\music`  
**Audio Set**: *The Concordia Organist* (Lutheran Service Book Accompaniment Set)

---

## 1. Executive Summary

- **Total Audio Files Currently in `/music`**: 375 `.m4a` files
- **Present Discs**: 12 Discs (1, 2, 3, 5, 7, 12, 14, 16, 18, 21, 23, 30)
- **Missing Discs**: 19 Discs (4, 6, 8, 9, 10, 11, 13, 15, 17, 19, 20, 22, 24, 25, 26, 27, 28, 29, 31)
- **Present LSB Hymns**: 244 Hymns indexed
- **Missing LSB Hymns**: 412 Hymns (between LSB 331 and LSB 986)

---

## 2. Present Discs Breakdown

| Disc # | Track Range | Indexed Hymn Range | Liturgical Season / Category | Status |
|---|---|---|---|---|
| **Disc 01** | Tracks 01–21 | LSB 331 – 351 | Advent | ✅ Present |
| **Disc 02** | Tracks 01–20 | LSB 352 – 371 | Christmas | ✅ Present |
| **Disc 03** | Tracks 01–23 | LSB 372 – 394 | Christmas / Epiphany | ✅ Present |
| **Disc 05** | Tracks 01–24 | LSB 413 – 436 | Lent | ✅ Present |
| **Disc 07** | Tracks 01–20 | LSB 454 – 473 | Easter | ✅ Present |
| **Disc 12** | Tracks 01–21 | LSB 558 – 578 | Justification & Sanctification | ✅ Present |
| **Disc 14** | Tracks 01–20 | LSB 603 – 623 | Holy Baptism | ✅ Present |
| **Disc 16** | Tracks 01–23 | LSB 643 – 665 | Trust & Refuge | ✅ Present |
| **Disc 18** | Tracks 01–25 | LSB 687 – 711 | Lord's Supper & Praise | ✅ Present |
| **Disc 21** | Tracks 01–60 | LSB 755 – 780 | Christian Home & Care | ✅ Present |
| **Disc 23** | Tracks 01–22 | LSB 804 – 825 | Praise & Thanksgiving | ✅ Present |
| **Disc 30** | Tracks 01–96 | DS1, DS2, DS3 Canticles | Liturgical Settings (Kyrie, Gloria, Sanctus, Agnus Dei, Nunc Dimittis) | ✅ Present |

---

## 3. Missing Discs & Hymn Ranges (LSB 331 - 986)

| Missing Disc # | Estimated Hymn Range | Key Missing Hymns | Liturgical Season / Category |
|---|---|---|---|
| ❌ **Disc 04** | LSB 395 – 412 | LSB 395, 400, 412 | Epiphany |
| ❌ **Disc 06** | LSB 437 – 453 | LSB 437, 440, 450 | Lent & Holy Week |
| ❌ **Disc 08** | LSB 474 – 495 | LSB 475, 480, 490 | Easter & Ascension |
| ❌ **Disc 09** | LSB 496 – 516 | LSB 500, 505, 510 | Pentecost & Holy Trinity |
| ❌ **Disc 10** | LSB 517 – 536 | LSB 520, 525, 530 | The Church & Word of God |
| ❌ **Disc 11** | LSB 537 – 557 | LSB 540, 545, 550 | Confession & Absolution |
| ❌ **Disc 13** | LSB 579 – 602 | **LSB 594** (*God's Own Child, I Gladly Say It*) | Stewardship & Christian Life |
| ❌ **Disc 15** | LSB 624 – 642 | LSB 625, 630, 640 | Confirmation & Vocation |
| ❌ **Disc 17** | LSB 666 – 686 | LSB 670, 675, 680 | Cross & Comfort |
| ❌ **Disc 19** | LSB 712 – 733 | LSB 715, 720, 730 | Evening & Burial |
| ❌ **Disc 20** | LSB 734 – 754 | LSB 740, 745, 750 | Nation & Morning |
| ❌ **Disc 22** | LSB 781 – 803 | LSB 785, 790, 800 | Society & Care |
| ❌ **Disc 24** | LSB 826 – 847 | **LSB 845** (*Where Charity and Love Prevail*) | Love & Charity |
| ❌ **Disc 25** | LSB 848 – 869 | **LSB 866** (*Lord Jesus Christ, the Children's Friend*) | Children & Family |
| ❌ **Disc 26** | LSB 870 – 891 | LSB 875, 880, 885 | Morning, Evening & Close of Service |
| ❌ **Disc 27** | LSB 892 – 915 | LSB 895, 900, 910 | Word of God & Worship |
| ❌ **Disc 28** | LSB 916 – 941 | LSB 920, 925, 935 | Praise & Doxology |
| ❌ **Disc 29** | LSB 942 – 986 | LSB 945, 960, 986 | Canticles & Additional Hymns |
| ❌ **Disc 31** | Liturgical Settings | DS4, DS5, Matins, Vespers, Compline | Liturgical Ordinaries (Part 2) |

---

## 4. Next Steps for Complete Coverage

1. Copy the missing **19 `.m4a` disc folders** (Discs 4, 6, 8, 9, 10, 11, 13, 15, 17, 19, 20, 22, 24, 25, 26, 27, 28, 29, 31) into `c:\dev\IdeaProjects\hymnody-manager\music`.
2. Click **"🔄 Rescan Catalog"** in the web app (or send a POST to `/api/scan`). All 650+ hymns (LSB 331 through 986) will automatically parse and become available for worship planning!
