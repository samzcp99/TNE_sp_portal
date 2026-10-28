const allTiles = [
    '1万', '2万', '3万', '4万', '5万', '6万', '7万', '8万', '9万',
    '1筒', '2筒', '3筒', '4筒', '5筒', '6筒', '7筒', '8筒', '9筒',
    '1条', '2条', '3条', '4条', '5条', '6条', '7条', '8条', '9条',
    '东', '南', '西', '北', '中', '发', '白'
];

const tileImages = {
    '1万': 'images/1m.png', '2万': 'images/2m.png', '3万': 'images/3m.png', '4万': 'images/4m.png', '5万': 'images/5m.png',
    '6万': 'images/6m.png', '7万': 'images/7m.png', '8万': 'images/8m.png', '9万': 'images/9m.png',
    '1筒': 'images/1p.png', '2筒': 'images/2p.png', '3筒': 'images/3p.png', '4筒': 'images/4p.png', '5筒': 'images/5p.png',
    '6筒': 'images/6p.png', '7筒': 'images/7p.png', '8筒': 'images/8p.png', '9筒': 'images/9p.png',
    '1条': 'images/1s.png', '2条': 'images/2s.png', '3条': 'images/3s.png', '4条': 'images/4s.png', '5条': 'images/5s.png',
    '6条': 'images/6s.png', '7条': 'images/7s.png', '8条': 'images/8s.png', '9条': 'images/9s.png',
    '东': 'images/1z.png', '南': 'images/2z.png', '西': 'images/3z.png', '北': 'images/4z.png',
    '中': 'images/7z.png', '发': 'images/6z.png', '白': 'images/5z.png'
};

let shuffledTiles = [];
let playerHand = [];
let selectedTile = null;
let lastDrawnTile = null;
let isGameOver = false;

function shuffleTiles() {
    shuffledTiles = [...allTiles, ...allTiles, ...allTiles, ...allTiles];
    for (let i = shuffledTiles.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledTiles[i], shuffledTiles[j]] = [shuffledTiles[j], shuffledTiles[i]];
    }
}

function dealTiles() {
    playerHand = shuffledTiles.splice(0, 13);
    displayPlayerHand();
    toggleButtons();
}

function sortHand(hand) {
    const order = allTiles;
    return hand.sort((a, b) => order.indexOf(a) - order.indexOf(b));
}

function displayPlayerHand() {
    const handContainer = document.getElementById('player-hand');
    handContainer.innerHTML = '';
    playerHand = sortHand(playerHand);

    playerHand.forEach(tile => {
        const tileElement = document.createElement('div');
        tileElement.classList.add('mahjong-tile');
        tileElement.style.backgroundImage = `url(${tileImages[tile]})`;
        tileElement.onclick = () => selectTile(tileElement, tile);
        handContainer.appendChild(tileElement);
    });
}

function displayLastDrawnTile(tile) {
    const container = document.getElementById('last-drawn-tile');
    container.innerHTML = '';
    const tileElement = document.createElement('div');
    tileElement.classList.add('mahjong-tile');
    tileElement.style.backgroundImage = `url(${tileImages[tile]})`;
    tileElement.onclick = () => selectTile(tileElement, tile);

    const arrowElement = document.createElement('div');
    arrowElement.classList.add('arrow');

    container.appendChild(arrowElement);
    container.appendChild(tileElement);
}

function selectTile(tileElement, tile) {
    if (selectedTile) selectedTile.classList.remove('active');
    tileElement.classList.add('active');
    selectedTile = tileElement;
}

function drawTile() {
    if (shuffledTiles.length > 0) {
        const drawnTile = shuffledTiles.pop();
        playerHand.push(drawnTile);
        lastDrawnTile = drawnTile;
        displayLastDrawnTile(drawnTile);
        displayPlayerHand();
    } else {
        alert('牌堆已空，游戏结束！');
        isGameOver = true;
        toggleButtons();
    }
}

function discardTile() {
    if (!selectedTile) {
        alert('请选择一张牌！');
        return;
    }

    const tile = Object.keys(tileImages).find(
        key => tileImages[key] === selectedTile.style.backgroundImage.slice(5, -2)
    );

    if (lastDrawnTile === tile) {
        lastDrawnTile = null;
        document.getElementById('last-drawn-tile').innerHTML = '';
    } else {
        const index = playerHand.indexOf(tile);
        if (index !== -1) playerHand.splice(index, 1);
    }

    selectedTile = null;
    displayPlayerHand();
    toggleButtons();
    drawTile();
}

function toggleButtons() {
    const drawButton = document.getElementById('draw-button');
    const discardButton = document.getElementById('discard-button');
    if (isGameOver) {
        drawButton.style.display = 'none';
        discardButton.style.display = 'none';
    } else if (playerHand.length === 14) {
        drawButton.style.display = 'none';
        discardButton.style.display = 'inline-block';
    } else {
        drawButton.style.display = 'inline-block';
        discardButton.style.display = 'none';
    }
}

document.getElementById('shuffle-button').onclick = () => {
    shuffleTiles();
    dealTiles();
};

document.getElementById('draw-button').onclick = drawTile;
document.getElementById('discard-button').onclick = discardTile;

shuffleTiles();
dealTiles();
