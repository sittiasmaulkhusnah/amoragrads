/* paket.js — data paket yang dipakai katalog.html dan detail.html.
   Ubah harga, deskripsi, atau foto di sini, dua halaman ikut berubah. */

var WA_NUMBER = "6281296772025";   /* format internasional, tanpa + atau 0 di depan */

var PACKAGES = [
  {
    id: "grads-1",
    badge: null,
    name: "Grads 1",
    people: "1 Orang",
    duration: "60 Menit",
    photos: "25 Foto Edit",
    price: "400.000",
    desc: "Family & friends, spot bebas, unlimited shoot, semua file soft di Google Drive.",
    img: "aset/paket 1.png",

    kicker: "Paket foto wisuda solo",
    subtitle: "1 Hour Session, 25 foto edit, Multiple spot.",
    long: "Sesi foto wisuda personal selama 1 jam di beberapa spot pilihan, dengan hasil edit yang natural dan hangat. Cocok buat kamu yang mau mengabadikan hari kelulusan dengan gaya sendiri, tanpa buru-buru.",
    gallery: ["aset/paket 1.png", "aset/dpaket 1.png", "aset/dpaket 2.png", "aset/dpaket 3.png"],
    faq: [
      { q: "Apakah paket ini bisa untuk berdua atau berteman?", a: "GRADS I dirancang untuk sesi solo. Kalau mau bareng keluarga atau teman, cek paket GRADS II atau Couple & Bestie ya." },
      { q: "Apakah bisa foto di beberapa lokasi?", a: "Bisa. Dalam 1 jam sesi, kamu bisa berpindah ke beberapa spot favorit selama masih di area yang sama." },
      { q: "Semua hasil foto diberikan lewat apa?", a: "25 foto hasil edit dikirim melalui Google Drive, maksimal 3 hari setelah sesi foto." }
    ]
  },
  {
    id: "grads-2",
    badge: null,
    name: "Grads 2",
    people: "1 Orang",
    duration: "60 Menit",
    photos: "35 Foto Edit",
    price: "450.000",
    desc: "Family & friends, spot bebas, unlimited shoot, semua file soft di Google Drive.",
    img: "aset/kpaket 2.jpeg",

    kicker: "Paket foto wisuda solo, upgrade",
    subtitle: "1 Hour Session, 35 foto edit, Multiple spot.",
    long: "Sama seperti Grads 1 tapi hasil edit lebih banyak. Sesi foto solo 1 jam dengan spot bebas dan unlimited shoot, lalu kamu dapat 35 foto hasil edit terbaik, dikirim lewat Google Drive.",
    gallery: ["aset/kpaket 2.jpeg", "aset/k2paket 1.jpeg", "aset/k2paket 2.jpeg", "aset/k2paket 3.jpeg"],
    faq: [
      { q: "Apa bedanya Grads 1 dan Grads 2?", a: "Sama-sama sesi solo 1 jam, bedanya cuma di jumlah foto edit: Grads 1 dapat 25 foto, Grads 2 dapat 35 foto." },
      { q: "Apakah bisa foto di beberapa lokasi?", a: "Bisa, spot bebas selama 1 jam sesi." },
      { q: "Hasilnya diberikan lewat apa?", a: "35 foto hasil edit dikirim melalui Google Drive." }
    ]
  },
  {
    id: "couple-bestie",
    badge: null,
    name: "Couple & Bestie",
    people: "2 Orang",
    duration: "60 Menit",
    photos: "60 Foto Edit",
    price: "700.000",
    desc: "Sesi untuk 2 orang, spot bebas, unlimited shoot, semua file soft di Google Drive.",
    img: "aset/kpaket 3.jpeg",

    kicker: "Paket foto wisuda berdua",
    subtitle: "Untuk 2 orang, 1 Hour Session, 60 foto edit.",
    long: "Sesi foto bareng pasangan atau sahabat yang wisuda bareng. 1 jam sesi dengan spot bebas dan unlimited shoot, hasil 60 foto edit untuk kalian berdua, semua file dikirim lewat Google Drive.",
    gallery: ["aset/kpaket 3.jpeg", "aset/k3paket 1.jpeg", "aset/k3paket 2.jpeg"],
    faq: [
      { q: "Apakah harus wisuda di hari yang sama?", a: "Sebaiknya iya, biar bisa foto bareng dalam satu sesi. Kalau beda hari, chat kami dulu untuk atur jadwalnya." },
      { q: "60 foto editnya dibagi rata?", a: "60 foto adalah total hasil edit untuk sesi kalian berdua, kombinasi foto bareng dan foto masing-masing." },
      { q: "Bisa nambah orang lagi?", a: "Paket ini untuk 2 orang. Kalau mau lebih dari itu, cek paket Group ya." }
    ]
  },
  {
    id: "group",
    badge: null,
    name: "Group",
    people: "5 Orang",
    duration: "90 Menit",
    photos: "Unlimited Foto Edit",
    price: "150.000",
    desc: "Group foto only, spot bebas, unlimited shoot & edit, semua file soft di Google Drive.",
    img: "aset/kpaket 4.jpeg",

    kicker: "Paket foto rame-rame",
    subtitle: "Untuk 5 orang, 1.5 Hour Session, unlimited foto edit.",
    long: "Sesi foto bareng geng atau squad, khusus foto grup (group foto only). Sesi 1,5 jam dengan spot bebas, unlimited shoot dan unlimited edit, semua file dikirim lewat Google Drive.",
    gallery: ["aset/kpaket 4.jpeg", "aset/k4paket 1.jpeg", "aset/k4paket 2.jpeg", "aset/k4paket 3.jpeg"],
    faq: [
      { q: "Apakah bisa foto personal juga?", a: "Paket ini group foto only. Kalau mau ada sesi personal juga, gabungkan dengan paket solo seperti Grads 1 atau Grads 2 ya." },
      { q: "Untuk berapa orang paket ini?", a: "Untuk 5 orang. Kalau jumlahnya lebih dari itu, chat kami dulu untuk cek penyesuaian harga." },
      { q: "Unlimited edited itu maksudnya?", a: "Semua foto hasil sesi akan diedit tanpa batas jumlah, bukan cuma dipilih sebagian." }
    ]
  },
  {
    id: "photo-video",
    badge: null,
    name: "Photo & Video",
    people: "1 Orang",
    duration: "120 Menit",
    photos: "Video Sinematik 1–2 Menit",
    price: "999.000",
    desc: "Termasuk cinematic video, spot bebas, family & friends, semua file soft di Google Drive.",
    img: "aset/kpaket 5.png",

    kicker: "Paket lengkap foto + video sinematik",
    subtitle: "2 Hour Session, foto dan video sinematik 1–2 menit.",
    long: "Paket paling lengkap: dokumentasi foto wisuda plus video sinematik berdurasi 1–2 menit. Sesi 2 jam dengan spot bebas, bisa bareng keluarga dan teman, semua file dikirim lewat Google Drive.",
    gallery: ["aset/kpaket 5.png"],
    faq: [
      { q: "Video sinematiknya seperti apa?", a: "Video highlight momen wisudamu berdurasi 1–2 menit dengan editing sinematik." },
      { q: "Fotonya dapat berapa?", a: "Chat kami dulu untuk detail jumlah foto edit di paket ini, biar disesuaikan sama kebutuhanmu." },
      { q: "Bisa bareng keluarga dan teman?", a: "Bisa, paket ini sudah termasuk sesi bareng keluarga dan teman." }
    ]
  },
  {
    id: "video-cinematic",
    badge: null,
    name: "Video Cinematic Only",
    people: "1 Orang",
    duration: "120 Menit",
    photos: "Video Sinematik 1–2 Menit",
    price: "650.000",
    desc: "Video sinematik saja, spot bebas, family & friends, semua file soft di Google Drive.",
    img: "aset/kpaket 6.png",

    kicker: "Video sinematik wisuda",
    subtitle: "2 Hour Session, video sinematik 1–2 menit.",
    long: "Cuma butuh video aja? Paket ini pas buat kamu. Sesi 2 jam dengan spot bebas, bisa bareng keluarga dan teman, hasil video sinematik 1–2 menit dikirim lewat Google Drive.",
    gallery: ["aset/kpaket 6.png"],
    faq: [
      { q: "Apakah dapat foto juga?", a: "Paket ini khusus video. Kalau mau sekalian dapat foto, cek paket Photo & Video ya." },
      { q: "Videonya berapa lama?", a: "Durasi video sinematik 1–2 menit." },
      { q: "Bisa request lagu tertentu?", a: "Bisa, chat kami dulu untuk diskusi konsep dan lagunya." }
    ]
  },
  {
    id: "eksklusif",
    badge: "By Owner",
    name: "Eksklusif",
    people: "1 Orang",
    duration: "90 Menit",
    photos: "40 Foto Edit",
    price: "600.000",
    desc: "Sesi privat, spot bebas, unlimited shoot & edit, prioritas jadwal, semua file soft di Google Drive.",
    img: "aset/kpaket 7.jpeg",

    kicker: "Paket privat, langsung ditangani owner",
    subtitle: "1.5 Hour Session, 40 foto edit, same day edit.",
    long: "Sesi eksklusif yang langsung ditangani owner Amora Grads. Ada sesi free meeting dulu untuk ngobrolin konsep, lalu sesi foto 1,5 jam dengan spot bebas, dan hasil 40 foto edit yang bisa kamu terima di hari yang sama (same day edit).",
    gallery: ["aset/kpaket 7.jpeg", "aset/k7paket 1.jpeg", "aset/k7paket 2.jpeg", "aset/k7paket 3.jpeg"],
    faq: [
      { q: "Apa bedanya paket Eksklusif dengan paket lain?", a: "Paket ini ditangani langsung oleh owner, ada sesi free meeting untuk diskusi konsep dulu, dan hasil editnya bisa selesai di hari yang sama (same day edit)." },
      { q: "Free meeting konsep itu apa?", a: "Sesi ngobrol dulu sebelum hari-H untuk bahas konsep, outfit, dan spot foto yang kamu mau." },
      { q: "Same day edit maksudnya?", a: "Hasil edit bisa kamu terima di hari yang sama dengan sesi foto, jadi nggak perlu nunggu lama." }
    ]
  }
];

function getPackage(id){
  for (var i = 0; i < PACKAGES.length; i++) {
    if (PACKAGES[i].id === id) return PACKAGES[i];
  }
  return null;
}

/* Link WhatsApp dengan pesan otomatis berisi nama paket */
function waLink(p){
  var text = "Halo Amora Grads, saya mau booking paket " + p.name + " (Rp " + p.price + "). Apakah jadwalnya masih tersedia?";
  return "https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(text);
}

/* Link WhatsApp untuk tanya-tanya soal paket */
function waChatLink(p){
  var text = "Halo Amora Grads, saya mau tanya-tanya soal paket " + p.name;
  return "https://wa.me/" + WA_NUMBER + "?text=" + encodeURIComponent(text);
}