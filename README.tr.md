# Samsung Odyssey G5 G55C (LS32CG552EUXUF) firmware araştırması

Bu depo, sahibine ait 32 inç Samsung Odyssey G5 G55C, tam model kodu
`LS32CG552EUXUF`, üzerinde yürütülen firmware tersine mühendislik çalışmasının
tekrarlanabilir araçlarını ve teknik bulgularını içerir. İncelenen temel sürüm
`M-C5500GGZA-1010.0[D43B]`'dir.

Ulaşılan güvenli sonuç küçüktür: firmware'de zaten bulunan gizli `MGA`
fabrika-kalibrasyon sayfası tek bir veri baytıyla görünür yapılmıştır.
Yürütülebilir kod, bootloader, EDID, kalibrasyon değerleri, tuş dispatcher'ı ve
flash bölüm yapısı değiştirilmemiştir.

> [!WARNING]
> Bu resmi Samsung güncellemesi değildir. Değiştirilmiş firmware monitörü
> kullanılamaz hâle getirebilir. Test cihazında yalnız USB güncelleme vardı;
> harici SPI kurtarma yoktu. Her işlemden önce [SAFETY.md](SAFETY.md) okunmalı.

![Mevcut 35 salt-okunur satırı gösteren açılmış MGA fabrika sayfası](docs/images/mga-menu-unlocked.jpg)

*Test edilen `LS32CG552EUXUF` üzerindeki donanım sonucu: supported baytı
açıldıktan sonra mevcut MGA sayfası 35 satırın tamamını çiziyor. Değerler
tasarım gereği salt-okunur kalıyor; bu proje onları düzenlenebilir yapmıyor.*

## Kamuya açık tekrarlanabilirlik sınırı

Firmware'den bağımsız SPARC araştırma emülatörü henüz bu sürüme dahil
değildir. Emülatörden elde edilen sonuçlar adresler, ham talimatlar, girdiler
ve gözlenen çıktılarla belgelenmiştir; ancak şu anda yalnız deterministik imaj
builder'ı, verifier ve güvenlik regresyon testleri kamuya açıktır. Emülatör
donanım doğrulamasının yerine geçmez, onu destekleyen kanıttır. Ayrıntılar:
[docs/TOOLS.md](docs/TOOLS.md).

## Kesinleşen sonuçlar

- Ana uygulama SPARC V8, 32-bit, big-endian çalışıyor.
- Test edilen cihazda joystick **YUKARI uzun basma**, mevcut MGA fabrika
  olayını açıyor.
- `MGA / Not supported` durumu tek bir kategori `supported` baytına bağlı:
  `VA 0x2A4A76`, dosya `0x2D2776`, `00 -> 01`.
- Bu bayt açıldığında stok renderer, firmware'deki 35 MGA satırını çiziyor.
- MGA değerleri değiştirilemiyor; descriptor türlerinde gerçek MGA
  okuma/yazma bağlantısı yok. Bu bir “yetki baytı” eksikliği değil, yarım
  bırakılmış firmware yoludur.
- MGA satırlarını kind 2/3'ten genel kind-4 bayt editörüne çevirmek emülatörde
  denendi ve güvensiz olduğu kesinleşti: ilişkisiz kalıcı ayar selector'larına
  yazıyor ve `0x2FE` gain aralığını sekiz bite kırpıyor.
- HDMI/DP EQ, çalışma zamanında otomatik link training kullanıyor. Flash
  tabloları manuel değer değil tarama adayları; 44/45 fabrika etiketlerinin
  değer/action descriptor'ı yok.
- Yanındaki Factory `Picture` kategorisi gerçek ve yazılabilir. Ancak
  görünürlük alanı normal OSD ile ortak olduğundan açılması normal Oyun ve
  Resim sekmelerini kaldırdı. Bu patch reddedildi.
- TCON FW/DATA, FPGA, PDIC ve Panel Timing maddeleri bu build'de çalışan
  handler/payload değil; string veya stub kalıntılarıdır.
- Local Dimming bu modelde güvenli açılabilir bölgesel karartma değildir;
  firmware tek global PWM arka ışık yolunu seçiyor.

## Son test edilen üretim

```text
Stok girdi
  dosya:    M-C5500GGZA-1010.0[D43B].img
  boyut:    3.449.760 bayt
  SHA-256:  2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7
  sum16:    D43B

Üretilen çıktı
  dosya:    M-C5500GGZA-1014.0[D440].img
  boyut:    3.449.760 bayt
  SHA-256:  815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350
  sum16:    D440
```

Stoktan yalnız iki bayt farklıdır:

| Dosya offset | Stok | Son | Anlam |
|---:|---:|---:|---|
| `0x273367` | `30` (`0`) | `34` (`4`) | Gömülü sürüm `1010.0 -> 1014.0` |
| `0x2D2776` | `00` | `01` | MGA kategorisi `supported` |

Normal OSD'yi etkileyen ortak Picture alanı `0x2D278D`, stok `00` değerinde
kalır.

Samsung firmware'i bu depoda dağıtılmaz. Kullanıcı kendi yasal ve SHA-256
değeri birebir eşleşen stok imajını sağlamalıdır:

```bash
python3 tools/build_mga_only.py /stok/M-C5500GGZA-1010.0[D43B].img
python3 tools/verify_mga_only.py \
  /stok/M-C5500GGZA-1010.0[D43B].img \
  output/M-C5500GGZA-1014.0[D440].img
```

Güvenlik kontrolleri Python `assert` ifadelerine dayanmaz ve optimize
çalıştırmada (`python3 -O`) etkin kalır. CI hem normal hem optimize Python
modunu test eder.

## Belgeler

- [Teknik harita ve disassembly kanıtları](docs/TECHNICAL.md)
- [Sürüme özel adres cetveli](docs/ADDRESS_LEDGER.md)
- [Deney günlüğü, sorunlar ve çözümleri](docs/INCIDENTS.md)
- [MGA ve Factory Picture davranışı](docs/MGA_AND_FACTORY_PICTURE.md)
- [Gizli özellik ve TCON kararları](docs/HIDDEN_FEATURES.md)
- [Çözülen MGA-yazma ve HDMI/DP-EQ soruları](docs/OPEN_QUESTIONS_RESOLVED.md)
- [Araçlar ve emülatör kapsamı](docs/TOOLS.md)
- [Test ve tekrarlanabilirlik](docs/VALIDATION.md)
- [Yayın öncesi kontrol listesi](docs/RELEASE_CHECKLIST.md)

## İddia edilmeyenler

- MGA değerleri düzenlenebilir yapılmadı.
- Yeni kod veya özel menü eklenmedi.
- TCON/FPGA/PDIC güncelleme işlevi açılmadı.
- Bir string'in varlığı donanım desteği kabul edilmedi.
- Başka firmware/model/panel sürümlerinde güvenli olduğu iddia edilmedi.
  Özellikle 27 inç `LS27CG552EUXUF`, doğrulanmış hedef değildir.
