// script.js - two-page flow; result stays until Close/Check Another clicked
const inputPage = document.getElementById("inputPage");
const resultPage = document.getElementById("resultPage");
const form = document.getElementById("symptomForm");
const input = document.getElementById("symptoms");
const resultText = document.getElementById("resultText");
const closeBtn = document.getElementById("closeBtn");
const checkAnotherBtn = document.getElementById("checkAnotherBtn");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const symptoms = input.value.trim();
  if (!symptoms) {
    alert("Please enter your symptoms.");
    return;
  }

  // show result page and keep it visible until user clicks a button
  inputPage.style.display = "none";
  resultPage.style.display = "block"; // ✅ changed from flex to block
  resultText.textContent = "⏳ Analyzing your symptoms...";

  try {
    const resp = await fetch("http://127.0.0.1:8000/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ symptoms }),
    });

    const data = await resp.json();
    if (resp.ok && data.suggestion) {
      resultText.textContent = data.suggestion;
    } else if (resp.ok && (data.response || data.result)) {
      // support different backend field names
      resultText.textContent = data.response || data.result;
    } else {
      resultText.textContent = "⚠️ Server returned an error: " + (data.detail || resp.status);
    }
  } catch (err) {
    console.error("Fetch error:", err);
    resultText.textContent = "⚠️ Network error. Is the backend running?";
  }
});

// Return to input page (only when user clicks)
function goBack() {
  input.value = "";
  resultPage.style.display = "none";
  inputPage.style.display = "block"; // ✅ changed from flex to block
}

closeBtn.addEventListener("click", goBack);
checkAnotherBtn.addEventListener("click", goBack);

// prevent accidental reload clearing the result
window.onbeforeunload = function() {
  return "Are you sure you want to leave? Your result will be lost.";
};
