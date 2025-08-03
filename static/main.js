let preparations = [];
let foods = [];
let gameInitialized = false; // To track if the game elements have been added

document.addEventListener('DOMContentLoaded', function() {
    Promise.all([
        fetch('/api/preparations').then(response => response.json()),
        fetch('/api/foods').then(response => response.json())
    ]).then(([preps, foodItems]) => {
        preparations = preps.map(p => p.name);
        foods = foodItems.map(f => f.name);
        populateListSection(); // Populate the list section with data from the API
    }).catch(err => {
        console.error("Failed to load data from API:", err);
        alert("Something went wrong while loading data: " + err.message);
    });

    const btn = document.getElementById('btn');
    const sound = document.getElementById('sound');
    const parentElement = document.querySelector('.parent');
    const footerElement = document.getElementById('footer');

    if (footerElement) {
        footerElement.style.color = "white";
    }

    if (btn) {
        btn.addEventListener('click', function() {
            if (sound) {
                sound.play();
            }

            if (!gameInitialized) {
                parentElement.insertAdjacentHTML('beforeend', '<div id="two" class="all"></div>');
                parentElement.insertAdjacentHTML('beforeend', '<div id="and"></div>');
                parentElement.insertAdjacentHTML('beforeend', '<div id="three" class="all"></div>');
                parentElement.insertAdjacentHTML('beforeend', '<div id="four" class="all"></div>');
                
                document.querySelectorAll('.all').forEach(el => {
                    el.style.border = "1px solid lightskyblue";
                });
                gameInitialized = true;
            }
            game();
        });
    }

    // Search functionality for lists
    const searchInput = document.getElementById('list-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function(event) {
            const searchTerm = event.target.value.toLowerCase().trim();
            let filteredPreparations = preparations; // Default to all if search is empty
            let filteredFoods = foods;         // Default to all if search is empty

            if (searchTerm) {
                if (preparations) {
                    filteredPreparations = preparations.filter(item => item.toLowerCase().includes(searchTerm));
                }
                if (foods) {
                    filteredFoods = foods.filter(item => item.toLowerCase().includes(searchTerm));
                }
            }
            populateListSection(filteredPreparations, filteredFoods);
        });
    }

    // Suggest new item button
    const suggestItemButton = document.getElementById('suggest-item-btn');
    if (suggestItemButton) {
        suggestItemButton.addEventListener('click', function() {
            const newItem = prompt("Enter a new food item or preparation method to suggest:");
            if (newItem && newItem.trim() !== "") {
                const trimmedItem = newItem.trim();
                fetch('/api/suggestions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item: trimmedItem, status: 'pending', date: new Date().toISOString() })
                })
                .then(response => {
                    if (!response.ok) throw new Error('Failed to submit suggestion.');
                    return response.json();
                })
                .then(data => alert(`Suggestion "${data.item}" submitted successfully!`))
                .catch(error => {
                    console.error("Error submitting suggestion:", error);
                    alert("Could not submit suggestion at this time.");
                });
            } else if (newItem !== null) { // User clicked OK but entered nothing or only spaces
                alert("Suggestion cannot be empty. Please enter a valid item.");
            }
            // If newItem is null, user clicked "Cancel" on the prompt, so do nothing.
        });
    }
});

function renderList(listElement, items, noMatchMessage = "No items match your search.") {
    if (!listElement) return;
    listElement.innerHTML = ''; // Clear existing items
    if (items && items.length > 0) {
        items.forEach(itemText => {
            const li = document.createElement('li');
            li.textContent = itemText;
            listElement.appendChild(li);
        });
    } else {
        const li = document.createElement('li');
        li.textContent = noMatchMessage;
        listElement.appendChild(li);
    }
}

function populateListSection(preparationsToShow = preparations, foodsToShow = foods) {
    const preparationsListElement = document.getElementById('preparations-list');
    const foodsListElement = document.getElementById('foods-list');

    const initialLoad = preparations.length === 0 && foods.length === 0;
    const noMatchMsg = initialLoad ? "Loading items..." : "No items match your search.";

    renderList(preparationsListElement, preparationsToShow, noMatchMsg);
    renderList(foodsListElement, foodsToShow, noMatchMsg);
}


function getPreperation() {
    // Ensure preparations are loaded
    if (!preparations || preparations.length === 0) return "Loading...";
    const varPreperation = preparations[Math.floor(Math.random() * preparations.length)];
    return varPreperation;
}

function getfood() {
    // Ensure foods are loaded
    if (!foods || foods.length === 0) return "Loading...";
    const varfood = foods[Math.floor(Math.random() * foods.length)];
    return varfood;
}

function game() {
    const oneElement = document.getElementById('one');
    const twoElement = document.getElementById('two');
    const threeElement = document.getElementById('three');
    const fourElement = document.getElementById('four');
    const andElement = document.getElementById('and');

    if (oneElement) oneElement.innerHTML = getPreperation();
    if (twoElement) twoElement.innerHTML = getfood();
    if (threeElement) threeElement.innerHTML = getPreperation();
    if (fourElement) fourElement.innerHTML = getfood();
    if (andElement) andElement.innerHTML = "and";
}