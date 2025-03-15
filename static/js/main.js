// Map Functionality
let map = null;
let markers = [];

function initMap(center = { lat: 40.7128, lng: -74.0060 }, zoom = 13) {
    map = L.map('map').setView([center.lat, center.lng], zoom);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);
}

function addMarker(lat, lng, popup) {
    const marker = L.marker([lat, lng]).addTo(map);
    if (popup) {
        marker.bindPopup(popup);
    }
    markers.push(marker);
    return marker;
}

function clearMarkers() {
    markers.forEach(marker => marker.remove());
    markers = [];
}

function drawServiceArea(center, radius) {
    L.circle([center.lat, center.lng], {
        color: '#2196F3',
        fillColor: '#2196F3',
        fillOpacity: 0.1,
        radius: radius * 1000 // Convert km to meters
    }).addTo(map);
}

// Form Validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;

    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('invalid');
            isValid = false;
        } else {
            input.classList.remove('invalid');
        }
    });

    return isValid;
}

// Dynamic Form Fields
function addServiceField() {
    const container = document.getElementById('services-container');
    const serviceCount = container.children.length;
    
    const serviceField = document.createElement('div');
    serviceField.className = 'service-field';
    serviceField.innerHTML = `
        <select name="service-${serviceCount}" required>
            <option value="">Select Service</option>
            <!-- Options will be populated dynamically -->
        </select>
        <input type="number" name="rate-${serviceCount}" placeholder="Hourly Rate" required>
        <button type="button" onclick="removeServiceField(this)">Remove</button>
    `;
    
    container.appendChild(serviceField);
}

function removeServiceField(button) {
    button.parentElement.remove();
}

// File Upload Preview
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('image-preview').src = e.target.result;
        };
        reader.readAsDataURL(input.files[0]);
    }
}

// Rating System
function setRating(rating) {
    document.getElementById('rating-value').value = rating;
    const stars = document.querySelectorAll('.star');
    stars.forEach((star, index) => {
        star.classList.toggle('active', index < rating);
    });
}

// Notifications
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Search and Filter
function filterJobs(filters) {
    const jobs = document.querySelectorAll('.job-card');
    
    jobs.forEach(job => {
        let visible = true;
        
        if (filters.category && job.dataset.category !== filters.category) {
            visible = false;
        }
        
        if (filters.minRate && parseInt(job.dataset.rate) < filters.minRate) {
            visible = false;
        }
        
        if (filters.maxDistance && parseInt(job.dataset.distance) > filters.maxDistance) {
            visible = false;
        }
        
        job.style.display = visible ? 'block' : 'none';
    });
}

// Chat Functions
function sendMessage(recipientId, message) {
    // This would typically make an API call to your backend
    fetch('/api/messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            recipient_id: recipientId,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            appendMessage(message, 'sent');
        }
    })
    .catch(error => {
        showNotification('Failed to send message', 'error');
    });
}

function appendMessage(message, type) {
    const chatContainer = document.querySelector('.chat-messages');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    messageElement.textContent = message;
    chatContainer.appendChild(messageElement);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Availability Calendar
function updateAvailability(date, timeSlot, available) {
    // This would typically make an API call to your backend
    fetch('/api/availability', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            date: date,
            time_slot: timeSlot,
            available: available
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification('Availability updated');
        }
    })
    .catch(error => {
        showNotification('Failed to update availability', 'error');
    });
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize map if element exists
    const mapElement = document.getElementById('map');
    if (mapElement) {
        initMap();
    }
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!validateForm(form.id)) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'error');
            }
        });
    });
    
    // File upload preview
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            previewImage(this);
        });
    }
    
    // Initialize filters
    const filterInputs = document.querySelectorAll('.filter-input');
    filterInputs.forEach(input => {
        input.addEventListener('change', () => {
            const filters = {
                category: document.getElementById('category-filter').value,
                minRate: document.getElementById('min-rate-filter').value,
                maxDistance: document.getElementById('max-distance-filter').value
            };
            filterJobs(filters);
        });
    });
}); 