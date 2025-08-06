// Global variables
let count = 0;           // Number of clicks during the test
let timer = null;        // Timer interval reference
let startTime = null;    // Timestamp when the test starts
let testStarted = false; // Flag to check if test is active
let lastCPS = 0;         // Store last CPS score for name submission

// DOM elements
const startBtn = document.getElementById('startBtn');               // "Start Test" button
const clickBtn = document.getElementById('clickBtn');               // Central "Click Here" button
const timerDisplay = document.getElementById('timer');              // Timer display area
const resultDisplay = document.getElementById('result');            // Area to show CPS result
const resetBtn = document.getElementById('resetBtn');               // "Reset Test" button
const nameInputContainer = document.getElementById('nameInputContainer'); // Name input section
const nameInput = document.getElementById('nameInput');             // Input box for user name
const submitName = document.getElementById('submitName');           // "Submit Name" button
const leaderboardItems = document.querySelectorAll('.leaderboard-item'); // List of leaderboard entries

// Animate leaderboard: fade in and rise one by one
function resetAnimation() {
  leaderboardItems.forEach((item, i) => {
    item.style.opacity = 0;
    item.style.transform = "translateY(20px)";
    setTimeout(() => {
      item.style.opacity = 1;
      item.style.transform = "translateY(0)";
    }, i * 100); // Staggered animation by 100ms each
  });
}
resetAnimation(); // Trigger animation on load and reset

// Start button click handler
startBtn.addEventListener('click', () => {
  clickBtn.style.display = 'inline-block';   // Show the main click button
  resultDisplay.textContent = '';            // Clear previous result
  timerDisplay.textContent = '';             // Reset timer text
  nameInputContainer.style.display = 'none'; // Hide name input if previously visible
});

// Click button handler (where user clicks to measure CPS)
clickBtn.addEventListener('click', () => {
  // If the test is already running, just increment the click count
  if (testStarted) {
    count++;
    return;
  }

  // First click starts the test
  count = 1;
  testStarted = true;
  startTime = Date.now();
  timerDisplay.textContent = '5.00';
  resultDisplay.textContent = '';
  nameInputContainer.style.display = 'none';

  // Start countdown timer that updates every 10ms
  timer = setInterval(() => {
    let elapsed = (Date.now() - startTime) / 1000;
    let remaining = (5 - elapsed).toFixed(2);
    timerDisplay.textContent = remaining > 0 ? remaining : '0.00';

    // End test after 5 seconds
    if (elapsed >= 5) {
      clearInterval(timer);
      testStarted = false;

      let cps = count / 5;
      lastCPS = cps;
      resultDisplay.textContent = `Your CPS: ${cps.toFixed(3)}`;
      clickBtn.style.display = 'none'; // Hide the main button

      // Submit score to server
      fetch('/submit_score', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cps })
      })
      .then(res => res.json())
      .then(data => {
        // If score is in top 10, prompt for name input
        if (data.top10) {
          nameInputContainer.style.display = 'block';
        }
      });
    }
  }, 10);
});

// Submit name to be added to leaderboard
submitName.addEventListener('click', () => {
  const name = nameInput.value.trim();
  if (!name) return;

  fetch('/submit_name', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, cps: lastCPS })
  })
  .then(res => res.json())
  .then(() => {
    // Hide name input and reload to show updated leaderboard
    nameInputContainer.style.display = 'none';
    location.reload();
  });
});

// Reset button click handler
resetBtn.addEventListener('click', () => {
  // Reset all values and UI
  count = 0;
  testStarted = false;
  clickBtn.style.display = 'none';
  resultDisplay.textContent = '';
  timerDisplay.textContent = '';
  nameInputContainer.style.display = 'none';
  nameInput.value = '';
  resetAnimation(); // Trigger leaderboard animation again
});