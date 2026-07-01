document.addEventListener("DOMContentLoaded", function () {
    const toast = document.getElementById("toast");

    if (toast) {
        // Show toast after slight delay
        setTimeout(() => {
            toast.classList.add("show");
        }, 500);

        // Hide toast after 4 seconds
        setTimeout(() => {
            toast.classList.remove("show");
        }, 4500);
    }
});