/** @odoo-module */

/**
 * Copyright © Lyra Network.
 * This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
 *
 * @author    Lyra Network (https://www.lyra.com/)
 * @copyright Copyright © Lyra Network
 * @license   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)
 */

import paymentForm from '@payment/js/payment_form';

let can_process_payment = true;
let popin = false;

paymentForm.include({
    init() {
        this._super(...arguments);

        // Update form token on amount update.
        $(document).ready(function() {
            if (typeof (KR) == 'undefined') {
                return;
            }

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
        });
    },

    _lyraGetInlineValues() {
        const radio = document.querySelector('input[name="o_payment_radio"]:checked');
        const inlineForm = this._getInlineForm(radio);
        const lyraInlineForm = inlineForm.querySelector('[name="o_lyra_element_container"]');

        return JSON.parse(
            lyraInlineForm.dataset['lyraInlineFormValues']
        );
    },

    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if ((typeof (KR) == "undefined") || (paymentMethodCode != "lyra")) {
            this._super(...arguments);

            return;
        }

        const inlineValues = this._lyraGetInlineValues();
        if (inlineValues.length == 0) {
            return;
        }

        // Set the flow to direct to avoid redirection to payment page on Odoo payment button clic.
        this._setPaymentFlow('direct');
        this._disableButton(false);

        var deliveryCarrier = document.querySelector('#delivery_carrier');
        if (deliveryCarrier !== null) {
            localStorage.removeItem('lyraFormToken');
            localStorage.removeItem('lyraFormTokenData');
        }

        // If there is already a stored token, check if payment data has changed.
        var formToken = localStorage.getItem('lyraFormToken');
        var tokenData = localStorage.getItem('lyraFormTokenData');
        if ((formToken !== null) && (tokenData == JSON.stringify(inlineValues))) {
            console.log('Payment details did not change on method display. Use the existing token.');

            this._lyraDisplayEmbeddedForm(formToken, inlineValues);
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
                    this._setPaymentFlow('redirect');
                    this._enableButton();
 
                    return;
                } else {
                    formToken = data["formToken"];
                    localStorage.setItem('lyraFormToken', formToken);
                    localStorage.setItem('lyraFormTokenData', JSON.stringify(inlineValues));
                }

                this._lyraDisplayEmbeddedForm(formToken, inlineValues);
            });
        }
    },

    _lyraDisplayEmbeddedForm(formToken, inlineValues) {
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

        if (inlineValues["compact"] === "1") {
            KR.setFormConfig({
                cardForm: { layout: "compact" },
                smartForm: { layout: "compact" },
            });
        }

        KR.setFormConfig({ formToken: formToken });
        KR.onFormReady(() =>
            this._enableButton()
        );
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'lyra') {
            await this._super(...arguments);
            return;
        }

        if (! can_process_payment) {
            return;
        }

        var formToken = localStorage.getItem('lyraFormToken');
        var inlineValues = this._lyraGetInlineValues();

        if (localStorage.getItem('lyraFormTokenData') == JSON.stringify(inlineValues)) {
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
                    this._setPaymentFlow('redirect');
                    this._enableButton();

                    return this._processRedirectFlow(...arguments);
                } else if (data["formToken"] == 'NO_UPDATE') {
                    console.log('Payment details did not change on payment submit. Use the existing token.');
                } else {
                    formToken =  data["formToken"];
                }
            });
        }

        await KR.setFormConfig({ formToken: formToken });
        this._lyraSubmitPayment();
    },

    _lyraSubmitPayment() {
        if (popin) {
            KR.openPopin();
        } else {
            KR.openSelectedPaymentMethod();
        }

        this._enableButton();
        can_process_payment = false;
    },

    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode == "lyra" && ! can_process_payment) {
            this._lyraSubmitPayment();

            return;
        }

        await this._super(...arguments);
    },
});