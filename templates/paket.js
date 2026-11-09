/* paket.js — DIBANGKITKAN DARI DATABASE oleh Django (app/views.py: paket_js).

var WA_NUMBER = "{{ wa_number }}";   /* format internasional, tanpa + atau 0 di depan */

var PACKAGES = {{ packages_json|safe }};

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