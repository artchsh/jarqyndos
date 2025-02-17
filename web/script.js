const API_URL = "";

const messageEl = document.getElementById("message");
const dbContentEl = document.getElementById("dbContent");

// Helper: show message
function showMessage(text) {
    messageEl.textContent = text;
    setTimeout(() => { messageEl.textContent = ''; }, 3000);
}

// Helper: call API to update database (simulate update by posting whole data)
async function updateDatabase(newData) {
    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(newData)
        });
        if (!response.ok) throw new Error("Network error");
        location.reload()
    } catch (error) {
        console.error("Error updating database:", error);
        showMessage("Error updating database.");
    }
}

// Function to fetch and render current database contents in a user-friendly way
async function fetchDatabase() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Network error");
        const data = await response.json();
        renderDatabase(data);
        return data;
    } catch (error) {
        console.error("Error fetching database:", error);
        dbContentEl.textContent = "Error fetching database.";
        return null;
    }
}

function renderDatabase(data) {
    // Render Users, Admin IDs, and each bot_info category as lists with Remove buttons.
    let html = `<h3>Users</h3><ul>`;
    data.users.forEach((user, index) => {
        html += `<li class="item">
                  <span>${user}</span>
                  <button onclick="removeItem('users', ${index})">Remove</button>
                </li>`;
    });
    html += `</ul>`;
    
    html += `<h3>Admin IDs</h3><ul>`;
    data.admin_ids.forEach((admin, index) => {
        html += `<li class="item">
                   <span>${admin}</span>
                   <button onclick="removeItem('admin_ids', ${index})">Remove</button>
                 </li>`;
    });
    html += `</ul>`;
    
    html += `<h3>Practices</h3><ul>`;
    (data.bot_info.practices || []).forEach((item, index) => {
        html += `<li class="item">
                   <span>${item.name} (${item.author || "no author"})</span>
                   <button onclick="removeBotItem('practices', ${index})">Remove</button>
                 </li>`;
    });
    html += `</ul>`;
    
    html += `<h3>Psychologists</h3><ul>`;
    (data.bot_info.psychologists || []).forEach((item, index) => {
        html += `<li class="item">
                   <span>${item.name} - ${item.specialty}</span>
                   <button onclick="removeBotItem('psychologists', ${index})">Remove</button>
                 </li>`;
    });
    html += `</ul>`;
    
    html += `<h3>Universities</h3><ul>`;
    (data.bot_info.universities || []).forEach((item, index) => {
        html += `<li class="item">
                   <span>${item.name}</span>
                   <button onclick="removeBotItem('universities', ${index})">Remove</button>
                 </li>`;
    });
    html += `</ul>`;
    
    html += `<h3>Contacts</h3><ul>`;
    (data.bot_info.contacts || []).forEach((item, index) => {
        html += `<li class="item">
                   <span>${item.phone} ${item.name ? "(" + item.name + ")" : ""}</span>
                   <button onclick="removeBotItem('contacts', ${index})">Remove</button>
                 </li>`;
    });
    html += `</ul>`;
    dbContentEl.innerHTML = html;
}

// Remove item from top-level arrays (users or admin_ids)
async function removeItem(category, index) {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Network error");
        const data = await response.json();
        data[category].splice(index, 1);
        await updateDatabase(data);
        showMessage(`Removed from ${category}.`);
        fetchDatabase();
    } catch (error) {
        console.error("Error removing item:", error);
    }
}

// Remove item from bot_info categories
async function removeBotItem(category, index) {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error("Network error");
        const data = await response.json();
        data.bot_info[category].splice(index, 1);
        await updateDatabase(data);
        showMessage(`Removed from ${category}.`);
        fetchDatabase();
    } catch (error) {
        console.error("Error removing bot item:", error);
    }
}

// Refresh database button handler
document.getElementById("refreshDb").addEventListener("click", fetchDatabase);

// Auto-collapse other details when one is opened
const detailsElements = document.querySelectorAll("details");
detailsElements.forEach((detail) => {
    detail.addEventListener("toggle", (e) => {
        if (detail.open) {
            detailsElements.forEach((d) => {
                if (d !== detail) d.open = false;
            });
        }
    });
});

// Submit handler for Practice
document.getElementById("formPractice").addEventListener("submit", async (e) => {
    e.preventDefault();
    const data = await fetchDatabase();
    const id = data.bot_info.practices.length;
    const dataToAdd = {
        id,
        name: document.getElementById("practiceName").value,
        content: document.getElementById("practiceContent").value,
        author: document.getElementById("practiceAuthor").value || null
    };
    data.bot_info.practices.push(dataToAdd);
    await updateDatabase(data)
});

// Submit handler for Psychologist
document.getElementById("formPsychologist").addEventListener("submit", async (e) => {
    e.preventDefault();
    const dataToAdd = {
        name: document.getElementById("psychName").value,
        specialty: document.getElementById("psychSpecialty").value,
        instagram: document.getElementById("psychInstagram").value,
        contacts: {
            phone: document.getElementById("psychContactPhone").value,
            name: document.getElementById("psychContactName").value || null
        },
        price: parseInt(document.getElementById("psychPrice").value, 10)
    };
    const data = await fetchDatabase();
    data.bot_info.psychologists.push(dataToAdd);
    await updateDatabase(data)
});

// Submit handler for University
document.getElementById("formUniversity").addEventListener("submit", async (e) => {
    e.preventDefault();
    const dataToAdd = {
        name: document.getElementById("uniName").value,
        instagram: document.getElementById("uniInstagram").value
    };
    const data = await fetchDatabase();
    data.bot_info.universities.push(dataToAdd);
    await updateDatabase(data)
});

// Submit handler for Contacts
document.getElementById("formContacts").addEventListener("submit", async (e) => {
    e.preventDefault();
    const dataToAdd = {
        phone: document.getElementById("contactPhone").value,
        name: document.getElementById("contactName").value || null,
        email: document.getElementById("contactEmail").value || null
    };
    const data = await fetchDatabase();
    data.bot_info.contacts.push(dataToAdd);
    await updateDatabase(data);
});

// Initial load of database data
fetchDatabase();