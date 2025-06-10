async function importPublicKey(pem) {
    // Remove header/footer and decode base64
    const pemHeader = "-----BEGIN PUBLIC KEY-----";
    const pemFooter = "-----END PUBLIC KEY-----";
    const pemContents = pem.replace(pemHeader, "").replace(pemFooter, "").replace(/\s+/g, '');
    const binaryDer = atob(pemContents);

    // Convert to ArrayBuffer
    const binaryArray = new Uint8Array(binaryDer.length);
    for (let i = 0; i < binaryDer.length; i++) {
        binaryArray[i] = binaryDer.charCodeAt(i);
    }

    // Import public key
    return await window.crypto.subtle.importKey(
        "spki",
        binaryArray.buffer,
        {
            name: "RSA-OAEP",
            hash: "SHA-256",
        },
        true,
        ["encrypt"]
    );
}
importPublicKey(`-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvxSfp7aa57u8Y+sNpvKe
StxvO2TwGjjniyU9es/wEeyr3nsER5jOJHaRm+zaCshclYGXmxpaUlxvrmN9BF/R
TyvIkZPTMNCsP8IHIypSvAutyGDIYEWWgTluKAAq9HqjPsw3XmRD0rS2osVK4VvE
FT+eAfVy2LNYB4+MHFEGuCKbxVHBDiAPJqmsB48TbBIMein3jrj+gfLR1un2x0PJ
BRN98R7pVHbAoJVHIC4qEipyO8jETGASK7LUK3M0aIkPfjzgzew0saF89tBdjPvC
BO0NUOfHuFOhfTtK394RgFFuLQpDCf+tIWn/ve2yilVu9QBivPbxnV+oNrm1RFkZ
0wIDAQAB
-----END PUBLIC KEY-----
`).then((key) => { window.currentPublicKey = key; });
async function encryptWithPublicKey(publicKey, message) {
    const encoder = new TextEncoder();
    const encoded = encoder.encode(message);
    const ciphertext = await window.crypto.subtle.encrypt(
        {
            name: "RSA-OAEP"
        },
        publicKey,
        encoded
    );
    return btoa(String.fromCharCode(...new Uint8Array(ciphertext)));
}
function getCookie(cname) {
    let name = cname + "=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for(let i = 0; i <ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
