const loginBox = document.querySelector("#login-content");
const form = document.querySelector("#login-content form");
const usernameBox = document.querySelector("#username");
const passwordBox = document.querySelector("#password");
const messageBox = document.querySelector("#message");
function loginSuccess(data) {
    const success = data.success;
    if (success) {
        messageBox.textContent = "Credentials were correct.";
    }
    else {
        switch (data.reason) {
            case "{{ exceptions.NotFoundError.identifier }}":
                messageBox.textContent = "User not found.";
                break;
            case "{{ exceptions.InvalidCredentials.identifier }}":
                messageBox.textContent = "Bad credentials.";
                break;
            default:
                messageBox.textContent = "Couldn't log in.";
        }
        
    }
    messageBox.style.visibility = "visible";
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("{{ url_for('login') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({ username: usernameBox.value, password: passwordBox.value })
    }).then((response) => response.json()).then(loginSuccess);
}, true);