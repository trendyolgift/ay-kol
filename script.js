async function checkPass() {
  const pass = document.getElementById("passcode").value.trim();
  const urlParams = new URLSearchParams(window.location.search);
  const chatID = urlParams.get("chat") || "default";

  const response = await fetch("data.json");
  const data = await response.json();

  if (data[chatID] && data[chatID] === pass) {
    document.getElementById("status").innerText = "Giriş başarılı!";
    // Buraya başarılı girişte ne yapılacaksa ekle (kamera aç vs.)
  } else {
    document.getElementById("status").innerText = "Yanlış şifre!";
  }
}
