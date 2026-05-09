(function (global) {
  "use strict";

  var GRID_SIZE = 16;
  var DIRECTIONS = {
    up: { x: 0, y: -1 },
    down: { x: 0, y: 1 },
    left: { x: -1, y: 0 },
    right: { x: 1, y: 0 }
  };
  var OPPOSITES = {
    up: "down",
    down: "up",
    left: "right",
    right: "left"
  };

  function makeInitialSnake(gridSize) {
    var center = Math.floor(gridSize / 2);
    return [
      { x: center, y: center },
      { x: center - 1, y: center },
      { x: center - 2, y: center }
    ];
  }

  function cloneSegment(segment) {
    return { x: segment.x, y: segment.y };
  }

  function keyForPoint(point) {
    return point.x + "," + point.y;
  }

  function isSamePoint(first, second) {
    return first.x === second.x && first.y === second.y;
  }

  function randomIndex(length, randomFn) {
    if (length <= 1) {
      return 0;
    }

    var value = randomFn();
    var index = Math.floor(value * length);
    return Math.min(length - 1, index);
  }

  function placeFood(gridSize, snake, randomFn) {
    var openCells = [];
    var occupied = new Set();

    snake.forEach(function (segment) {
      occupied.add(keyForPoint(segment));
    });

    for (var y = 0; y < gridSize; y += 1) {
      for (var x = 0; x < gridSize; x += 1) {
        var candidate = { x: x, y: y };

        if (!occupied.has(keyForPoint(candidate))) {
          openCells.push(candidate);
        }
      }
    }

    if (openCells.length === 0) {
      return null;
    }

    return openCells[randomIndex(openCells.length, randomFn)];
  }

  function createInitialState(options) {
    var settings = options || {};
    var gridSize = settings.gridSize || GRID_SIZE;
    var randomFn = settings.randomFn || Math.random;
    var snake = makeInitialSnake(gridSize);

    return {
      gridSize: gridSize,
      snake: snake,
      direction: "right",
      pendingDirection: "right",
      food: placeFood(gridSize, snake, randomFn),
      score: 0,
      gameOver: false,
      won: false,
      paused: false,
      started: false
    };
  }

  function setDirection(state, nextDirection) {
    if (!DIRECTIONS[nextDirection] || state.gameOver) {
      return state;
    }

    if (nextDirection === OPPOSITES[state.direction]) {
      return state;
    }

    return {
      gridSize: state.gridSize,
      snake: state.snake.slice(),
      direction: state.direction,
      pendingDirection: nextDirection,
      food: state.food ? cloneSegment(state.food) : null,
      score: state.score,
      gameOver: state.gameOver,
      won: state.won,
      paused: false,
      started: true
    };
  }

  function togglePause(state) {
    if (!state.started || state.gameOver) {
      return state;
    }

    return {
      gridSize: state.gridSize,
      snake: state.snake.slice(),
      direction: state.direction,
      pendingDirection: state.pendingDirection,
      food: state.food ? cloneSegment(state.food) : null,
      score: state.score,
      gameOver: state.gameOver,
      won: state.won,
      paused: !state.paused,
      started: state.started
    };
  }

  function tick(state, randomFn) {
    if (state.gameOver || state.paused || !state.started) {
      return state;
    }

    var nextDirection = state.pendingDirection;
    var vector = DIRECTIONS[nextDirection];
    var head = state.snake[0];
    var nextHead = {
      x: head.x + vector.x,
      y: head.y + vector.y
    };
    var hitsWall =
      nextHead.x < 0 ||
      nextHead.y < 0 ||
      nextHead.x >= state.gridSize ||
      nextHead.y >= state.gridSize;

    if (hitsWall) {
      return {
        gridSize: state.gridSize,
        snake: state.snake.slice(),
        direction: nextDirection,
        pendingDirection: nextDirection,
        food: state.food ? cloneSegment(state.food) : null,
        score: state.score,
        gameOver: true,
        won: false,
        paused: false,
        started: true
      };
    }

    var ateFood = state.food && isSamePoint(nextHead, state.food);
    var bodyToCheck = ateFood ? state.snake : state.snake.slice(0, -1);
    var collidedWithSelf = bodyToCheck.some(function (segment) {
      return isSamePoint(segment, nextHead);
    });

    if (collidedWithSelf) {
      return {
        gridSize: state.gridSize,
        snake: state.snake.slice(),
        direction: nextDirection,
        pendingDirection: nextDirection,
        food: state.food ? cloneSegment(state.food) : null,
        score: state.score,
        gameOver: true,
        won: false,
        paused: false,
        started: true
      };
    }

    var nextSnake = [nextHead].concat(
      state.snake.map(function (segment) {
        return cloneSegment(segment);
      })
    );

    if (!ateFood) {
      nextSnake.pop();
    }

    var won = nextSnake.length === state.gridSize * state.gridSize;

    return {
      gridSize: state.gridSize,
      snake: nextSnake,
      direction: nextDirection,
      pendingDirection: nextDirection,
      food: ateFood && !won
        ? placeFood(state.gridSize, nextSnake, randomFn || Math.random)
        : ateFood
          ? null
          : state.food
            ? cloneSegment(state.food)
            : null,
      score: ateFood ? state.score + 1 : state.score,
      gameOver: won,
      won: won,
      paused: false,
      started: true
    };
  }

  global.SnakeLogic = {
    GRID_SIZE: GRID_SIZE,
    DIRECTIONS: DIRECTIONS,
    createInitialState: createInitialState,
    placeFood: placeFood,
    setDirection: setDirection,
    tick: tick,
    togglePause: togglePause
  };
})(window);
