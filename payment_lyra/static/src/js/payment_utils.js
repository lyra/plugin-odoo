/** @odoo-module */

/**
 * Copyright © Lyra Network.
 * This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
 *
 * @author    Lyra Network (https://www.lyra.com/)
 * @copyright Copyright © Lyra Network
 * @license   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)
 */

let popin = false;

export function lyraCheckAmount() {
    var observer = new MutationObserver( function(mutations) {
        mutations.forEach((mutation) => {
            const checkedRadio = document.querySelectorAll("[data-payment-method-code='lyra']")[0];
            if (checkedRadio && checkedRadio.checked) {
                console.log("Amount total sumary has changed. We may have to re-create form token.");
                checkedRadio.click();
            }
        });
    });

    // Configure and start observing the target element for changes in child nodes.
    var config = { characterData: true, childList: true, subtree: true };

    var amount_total_summary = document.querySelector('#amount_total_summary');
    observer.observe(amount_total_summary, config);
}

export function lyraHidePreMessage() {
    if ($('#lyra-embedded-wrapper').length > 0) {
        let paymentOption = document.querySelector('input[data-provider-code="lyra"]');
        if (paymentOption) {
            parent = paymentOption.parentElement.parentElement.parentElement;
            let elem = parent.children[1];

            if (parent.nextElementSibling.contains($('#lyra-embedded-wrapper')[0])) {
                elem.textContent = '';
            }
        }
    }
}

export async function lyraPrepareInlineForm(inlineValues) {
    var deliveryCarrier = document.querySelector('#delivery_carrier');
    if (deliveryCarrier !== null) {
        localStorage.removeItem('lyraFormToken');
        localStorage.removeItem('lyraFormTokenData');
    }

    // If there is already a stored token, check if payment data has changed.
    var formToken = getLyraItem('lyraFormToken');
    var tokenData = getLyraItem('lyraFormTokenData');
    if ((formToken !== null) && (tokenData == JSON.stringify(inlineValues))) {
        console.log('Payment details did not change on method display. Use the existing token.');
        lyraDisplayEmbeddedForm(formToken, inlineValues);
    } else {
        await fetch('/payment/lyra/createFormToken', {
            method: "POST",
            headers: {
                "Content-Type":"application/json",
            },
            body: JSON.stringify(inlineValues),
        }).then(response => { return response.json() })
            .then(data => {
            // If form token was not created , fallback to redirection mode.
            if (data["formToken"] === false) {
                return;
            } else {
                formToken = data["formToken"];
                setLyraItem('lyraFormToken', formToken, 15*60*1000);
                setLyraItem('lyraFormTokenData', JSON.stringify(inlineValues), 15*60*1000);
            }

            lyraDisplayEmbeddedForm(formToken, inlineValues);
        });
    }
}

async function lyraDisplayEmbeddedForm(formToken, inlineValues) {
    // Create a div for embedded form.
    let embeddedDiv = document.createElement("div");
    embeddedDiv.setAttribute("class", "kr-smart-form");

    if (inlineValues["pop_in"] === "1") {
        popin = true;
        embeddedDiv.setAttribute("kr-popin", "");
        document.getElementById("lyra-embedded-wrapper").appendChild(embeddedDiv);
    } else {
        embeddedDiv.setAttribute("kr-single-payment-button", "");
    }

    if (inlineValues["entry_mode"] === "embedded_extended_with_logos" || inlineValues["entry_mode"] === "embedded_extended_without_logos") {
        embeddedDiv.setAttribute("kr-card-form-expanded", "");
        if (inlineValues["entry_mode"] === "embedded_extended_without_logos") {
            embeddedDiv.setAttribute("kr-no-card-logo-header", "");
        }
    }

    document.getElementById("lyra-embedded-wrapper").appendChild(embeddedDiv);

    var __vadsFormConfig = { formToken: formToken };
    if (inlineValues["compact"] === "1") {
        __vadsFormConfig['cardForm'] = { layout: 'compact' };
        __vadsFormConfig['smartForm']= { layout: 'compact'};
    }

    await KR.setFormConfig(__vadsFormConfig);
}

export async function lyraProcessDirectFlow(inlineValues, processingValues) {
    var formToken = getLyraItem('lyraFormToken');

    if (getLyraItem('lyraFormTokenData') == JSON.stringify(inlineValues)) {
        console.log('Payment details did not change on payment submit. Use the existing token.');
    } else {
        await fetch('/payment/lyra/createFormToken', {
            method: "POST",
            headers: {
                "Content-Type":"application/json",
            },
            body: JSON.stringify(processingValues),
        }).then(response => { return response.json() })
            .then(async data => {
            if (! data["formToken"]) {
                console.log('Error while creating form token.');
            } else if (data["formToken"] == 'NO_UPDATE') {
                console.log('Payment details did not change on payment submit. Use the existing token.');
            } else {
                formToken = data["formToken"];
            }
        });
    }

    if (formToken) {
        await KR.setFormConfig({ formToken: formToken });
        lyraSubmitPayment();
    }
}

export function lyraSubmitPayment() {
    if (popin) {
        KR.openPopin();
    } else {
        KR.openSelectedPaymentMethod();
    }
}

function setLyraItem(key, value, ttl) {
    let item = {
        value: value,
        expiry: ttl ? Date.now() + ttl : null
    };

    localStorage.setItem(key, JSON.stringify(item));
}

function getLyraItem(key) {
    let item = localStorage.getItem(key);

    // if the item doesn't exist, return null
    if (!item) {
        return null;
    }

    try {
        item = JSON.parse(item);
    } catch (e) {
        return null;
    }

    // Compare the expiry time of the item with the current time.
    if (item.expiry && Date.now() > item.expiry) {
        // If the item is expired, delete the item from storage and return null
        localStorage.removeItem(key);
        return null;
    }

    return item.value;
}