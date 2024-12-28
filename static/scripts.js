document.addEventListener("DOMContentLoaded", function () {
  const myModal = document.getElementById("gameModal");
  const myInput = document.getElementById("myInput");

  if (myModal) {
    myModal.addEventListener("shown.bs.modal", () => {
      if (myInput) {
        myInput.focus();
      }
    });
  }

  if (typeof bootstrap === "undefined") {
    console.error("Bootstrap is not loaded");
  } else {
    console.log("Bootstrap is loaded");
  }

  // Add event listeners for buttons
  document.querySelectorAll('.btn-primary[data-bs-toggle="modal"]').forEach(button => {
    button.addEventListener('click', function () {
      const gameId = this.getAttribute('data-game-id');
      callGameData(gameId);
    });
  });
});

function callGameData(id) {
  fetch(`/game_data/${id}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      console.log(data);
      document.getElementById("gameModalLabel").innerText = data.title;
      document.querySelector(".modal-body").innerText = data.description;
    })
    .catch((error) => {
      console.error("Error:", error);
      document.getElementById("gameModalLabel").innerText = "Error";
      document.querySelector(".modal-body").innerText = "Failed to load game data.";
    });
}