<script>
    // This script creates an age verification modal for users who must be 21 or older.

    // Wait for the page to fully load before executing the script
    document.addEventListener('DOMContentLoaded', function () {
        // Create the modal element
        const ageModal = document.createElement('div');

        // Set an ID for the modal for easy reference
        ageModal.id = 'ageVerificationModal';

        // Add styles to the modal for a full-page overlay
        ageModal.style = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85); /* Semi-transparent black */
            color: white;
            z-index: 10000; /* Ensure it appears on top of everything */
            display: flex;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        `;

        // Define the content of the modal (text, buttons, and styles)
        ageModal.innerHTML = `
            <div style="text-align: center; background: #333; padding: 30px 20px; border-radius: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.5); width: 90%; max-width: 400px;">
                <h2 style="margin-bottom: 20px; font-size: 24px;">Are you at least 21 years old?</h2>
                <p style="margin-bottom: 30px; font-size: 16px; line-height: 1.5; color: #ddd;">
                    You must confirm your age to access this site. Please click "Yes" if you're 21 or older, or "No" to exit.
                </p>
                <!-- Button to confirm user is 21+ -->
                <button onclick="acceptAgeVerification()" 
                    style="padding: 12px 20px; font-size: 16px; cursor: pointer; background: #4CAF50; border: none; border-radius: 5px; color: white; margin: 5px; transition: background 0.3s;">
                    Yes, I am 21+
                </button>
                <!-- Button to deny access -->
                <button onclick="denyAgeVerification()" 
                    style="padding: 12px 20px; font-size: 16px; cursor: pointer; background: #F44336; border: none; border-radius: 5px; color: white; margin: 5px; transition: background 0.3s;">
                    No, I am under 21
                </button>
            </div>
        `;

        // Append the modal to the document body so it appears immediately
        document.body.appendChild(ageModal);

        // Disable scrolling while the modal is visible
        document.body.style.overflow = 'hidden';
    });

    // Function to handle "Yes" button click (allow access)
    function acceptAgeVerification() {
        const modal = document.getElementById('ageVerificationModal');
        modal.style.display = 'none'; // Hide the modal
        document.body.style.overflow = ''; // Re-enable scrolling
    }

    // Function to handle "No" button click (deny access)
    function denyAgeVerification() {
        // Redirect to a "Sorry" page or an external URL
        window.location.href = 'https://www.google.com';
    }
</script>
