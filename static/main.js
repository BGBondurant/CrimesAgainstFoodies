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

        // Fetch and display the daily image once the main data is loaded
        fetchDailyImage();
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
            const filterList = (list) => searchTerm ? list.filter(item => item.toLowerCase().includes(searchTerm)) : list;
            
            const filteredPreparations = filterList(preparations);
            const filteredFoods = filterList(foods);

            populateListSection(filteredPreparations, filteredFoods);
        });
    }

    // Suggest new item button
    const suggestItemButton = document.getElementById('suggest-item-btn');
    const suggestionTypeSelect = document.getElementById('suggestion-type-select');
    if (suggestItemButton && suggestionTypeSelect) {
        suggestItemButton.addEventListener('click', function() {
            const newItem = prompt("Enter a new food item or preparation method to suggest:");
            if (newItem && newItem.trim() !== "") {
                const trimmedItem = newItem.trim();
                const itemType = suggestionTypeSelect.value;
                fetch('/api/suggestions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ item: trimmedItem, status: 'pending', date: new Date().toISOString(), type: itemType })
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

function fetchDailyImage() {
    const container = document.getElementById('daily-image-container');
    if (!container) return;

    fetch('/api/daily-image')
        .then(response => {
            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('No daily image has been generated yet. Check back tomorrow!');
                }
                throw new Error('Could not fetch the daily image.');
            }
            return response.json();
        })
        .then(data => {
            container.innerHTML = `
                <img src="${data.image_url}" alt="AI generated image for '${data.prompt}'" class="daily-image">
                <p class="daily-image-prompt">Today's inspiration: <strong>${data.prompt}</strong></p>
            `;
            // Update social media links to share the image and prompt
            updateSocialLinks(data.prompt, data.image_url);
        })
        .catch(error => {
            container.innerHTML = `<p class="error-message">${error.message}</p>`;
            console.error('Error fetching daily image:', error);
        });
}

function updateSocialLinks(prompt, imageUrl) {
    const text = `Check out this AI-generated food crime: ${prompt}! #CrimesAgainstFoodies`;
    const pageUrl = window.location.href;

    const twitterLink = document.getElementById('share-twitter');
    if (twitterLink) {
        twitterLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(pageUrl)}`;
    }

    const facebookLink = document.getElementById('share-facebook');
    if (facebookLink) {
        facebookLink.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(pageUrl)}&quote=${encodeURIComponent(text)}`;
    }

    const pinterestLink = document.getElementById('share-pinterest');
    if (pinterestLink) {
        pinterestLink.href = `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(pageUrl)}&media=${encodeURIComponent(imageUrl)}&description=${encodeURIComponent(text)}`;
    }
}

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