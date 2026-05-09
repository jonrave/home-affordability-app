(function () {
  "use strict";

  var boardElement = document.getElementById("board");
  var scoreElement = document.getElementById("score");
  var statusElement = document.getElementById("status");
  var pauseButton = document.getElementById("pause-button");
  var restartButton = document.getElementById("restart-button");
  var directionButtons = document.querySelectorAll("[data-direction]");
  var logic = window.SnakeLogic;
  var state = logic.createInitialState();
  var cells = new Map();
  var TICK_MS = 140;

  function cellKey(point) {
    return point.x + "," + point.y;
  }

  function buildBoard(gridSize) {
    boardElement.innerHTML = "";
    boardElement.style.setProperty("--grid-size", String(gridSize));
    cells.clear();

    for (var y = 0; y < gridSize; y += 1) {
      for (var x = 0; x < gridSize; x += 1) {
        var cell = document.createElement("div");
        cell.className = "cell";
        cell.setAttribute("role", "gridcell");
        boardElement.appendChild(cell);
        cells.set(cellKey({ x: x, y: y }), cell);
      }
    }
  }

  function messageForState(nextState) {
    if (nextState.won) {
      return "You filled the board. Press Restart to play again.";
    }

    if (nextState.gameOver) {
      return "Game over. Press Restart or R to try again.";
    }

    if (!nextState.started) {
      return "Press an arrow key, WASD, or tap a direction to start.";
    }

    if (nextState.paused) {
      return "Paused. Press Space or Resume to continue.";
    }

    return "Eat the food, avoid the walls, and do not run into yourself.";
  }

  function render(nextState) {
    scoreElement.textContent = String(nextState.score);
    statusElement.textContent = messageForState(nextState);
    pauseButton.textContent = nextState.paused ? "Resume" : "Pause";
    pauseButton.disabled = !nextState.started || nextState.gameOver;
    boardElement.classList.toggle("board--game-over", nextState.gameOver);

    cells.forEach(function (cell) {
      cell.className = "cell";
    });

    if (nextState.food) {
      var foodCell = cells.get(cellKey(nextState.food));

      if (foodCell) {
        foodCell.classList.add("cell--food");
      }
    }

    nextState.snake.forEach(function (segment, index) {
      var cell = cells.get(cellKey(segment));

      if (!cell) {
        return;
      }

      cell.classList.add("cell--snake");

      if (index === 0) {
        cell.classList.add("cell--head");
      }
    });
  }

  function applyDirection(direction) {
    state = logic.setDirection(state, direction);
    render(state);
  }

  function restartGame() {
    state = logic.createInitialState();
    render(state);
  }

  function handleKeydown(event) {
    var key = event.key.toLowerCase();
    var directionMap = {
      arrowup: "up",
      w: "up",
      arrowdown: "down",
      s: "down",
      arrowleft: "left",
      a: "left",
      arrowright: "right",
      d: "right"
    };

    if (directionMap[key]) {
      event.preventDefault();
      applyDirection(directionMap[key]);
      return;
    }

    if (key === " ") {
      event.preventDefault();
      state = logic.togglePause(state);
      render(state);
      return;
    }

    if (key === "r") {
      event.preventDefault();
      restartGame();
    }
  }

  buildBoard(state.gridSize);
  render(state);

  window.setInterval(function () {
    state = logic.tick(state);
    render(state);
  }, TICK_MS);

  document.addEventListener("keydown", handleKeydown);

  pauseButton.addEventListener("click", function () {
    state = logic.togglePause(state);
    render(state);
  });

  restartButton.addEventListener("click", restartGame);

  directionButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      applyDirection(button.dataset.direction);
    });
  });
})();
