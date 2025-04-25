const loginBox = document.querySelector("#signup-content");
const form = document.querySelector("#signup-content form");
const usernameBox = document.querySelector("#username");
const passwordBox = document.querySelector("#password");
const messageBox = document.querySelector("#message");
function signupSuccess(data) {
    const success = data.success;
    if (success) {
        messageBox.textContent = "Signup credentials were correct.";
    }
    else {
        switch (data.reason) {
            case "{{ exceptions.CannotBeNamedAnonymous.identifier }}":
                messageBox.textContent = "Username cannot be Anonymous in any case.";
                break;
            case "{{ exceptions.UsernameInvalidCharacters.identifier }}":
                messageBox.textContent = "Username must consist of characters a-z, A-Z, 0-9, _ and -.";
                break;
            case "{{ exceptions.PasswordTooLong.identifier }}":
                messageBox.textContent = "Password has to have a reasonable length.";
                break;
            case "{{ exceptions.PasswordTooShort.identifier }}":
                messageBox.textContent = "Password has to be longer.";
                break;
            case "{{ exceptions.UsernameTooLong.identifier }}":
                messageBox.textContent = "Username has to have a reasonable length.";
                break;
            case "{{ exceptions.UsernameTooShort.identifier }}":
                messageBox.textContent = "Username has to be longer.";
                break;
            case "{{ exceptions.UserSlotTakenError.identifier }}":
                messageBox.textContent = "That user slot is already taken.";
                break;
            case "{{ exceptions.AlreadyExistsError.identifier }}":
                messageBox.textContent = "That username is already taken.";
                break;
            default:
                messageBox.textContent = "Your account couldn't be created.";
        }
        
    }
    messageBox.style.visibility = "visible";
}
form.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("{{ url_for('register') }}", {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        method: "POST",
        body: JSON.stringify({ username: usernameBox.value, password: passwordBox.value })
    }).then((response) => response.json()).then(signupSuccess);
}, true);