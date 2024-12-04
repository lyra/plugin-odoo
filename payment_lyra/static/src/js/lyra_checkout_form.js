/**
 * Copyright © Lyra Network.
 * This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
 *
 * @author    Lyra Network (https://www.lyra.com/)
 * @copyright Copyright © Lyra Network
 * @license   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)
 */

document.addEventListener("DOMContentLoaded", function(event) {
    if (typeof (KR) == 'undefined') {
        return;
    }

  if ($('#kr-smart-form-parent').length > 0) {
    let elements = $('input[data-provider="lyra"]');
    elements.forEach(hidePreMessage);

        function hidePreMessage(element) {
           parent = element.parentElement.parentElement;
           let elem = parent.children[2];

           if (parent.nextElementSibling.contains($('#kr-smart-form-parent')[0])) {
              elem.textContent = '';
           }
        }
    }

    odoo.define('lyra_payment.lyra_checkout_form', require => {
        'use strict';

        const Lyra_PaymentCheckoutForm = require('payment.checkout_form');
        const Lyra_manageForm = require('payment.manage_form');
        let can_process_payment = true;
        let popin = false;

        const lyra_Mixin = {
            _prepareInlineForm: async function(code, paymentOptionId, flow) {
                if (code != "lyra") {
                    return this._super(...arguments);
                }
 
                if (! can_process_payment) {
                   return;
                }

                // Set the flow to direct to avoid redirection to payment page on Odoo payment button clic.
                this._disableButton(false);
                this._setPaymentFlow('direct');

                let paymentContext = { amount: this.txContext.amount, currencyId: this.txContext.currencyId, paymentOptionId: paymentOptionId, partnerId: this.txContext.partnerId };

                await fetch('/payment/lyra/getTemporaryFormToken', {
                    method: "POST",
                    headers: {
                        "Content-Type":"application/json",
                    },
                    body: JSON.stringify(paymentContext),
                }).then(response => { return response.json() })
                .then(data => {
                    // If form token was not created , fallback to redirection mode.
                    if (data["formToken"] === false) {
                        this._setPaymentFlow('redirect');
                        this._enableButton();

                        return;
                    }

                    // Create Smartform DIV.
                    let smartformDiv = document.createElement("div");
                    smartformDiv.setAttribute("class", "kr-smart-form");

                    if (data["popin"] === "yes") {
                        popin = true;
                        smartformDiv.setAttribute("kr-popin", "");
                        document.getElementById("kr-smart-form-parent").appendChild(smartformDiv);
                    } else {
                        smartformDiv.setAttribute("kr-single-payment-button", "");
                    }

                    if (data["dataEntryMode"] === "smartform_extended_with_logos" || data["dataEntryMode"] === "smartform_extended_without_logos") {
                        smartformDiv.setAttribute("kr-card-form-expanded", "");
                        if (data["dataEntryMode"] === "smartform_extended_without_logos") {
                            smartformDiv.setAttribute("kr-no-card-logo-header", "");
                        }
                    }

                    document.getElementById("kr-smart-form-parent").appendChild(smartformDiv);

                    if (data["compact"] === "1") {
                        KR.setFormConfig({
                            cardForm: { layout: "compact" },
                            smartForm: { layout: "compact" },
                        });
                    }

                    $(".card-footer").show();

                    KR.setFormConfig({ formToken: data["formToken"], publicKey: data["publicKey"] });
                    KR.onFormReady(() =>
                        this._enableButton()
                    );
                });
            },

            _processDirectPayment: async function(code, providerId, processingValues) {
                await fetch('/payment/lyra/refreshFormToken', {
                    method: "POST",
                    headers: {
                        "Content-Type":"application/json",
                    },
                    body: JSON.stringify(processingValues),
                }).then(response => { return response.json() })
                .then(async data => {
                    if (! data["formToken"]) {
                        this._setPaymentFlow('redirect');
                        this._enableButton();

                        return this._processRedirectPayment(code, providerId, processingValues);
                    }

                    await KR.setFormConfig({ formToken: data["formToken"] });
                    this._lyraSubmitPayment();
                });
            },

            _lyraSubmitPayment: function () {
                if (popin) {
                    KR.openPopin();
                    $(".card-footer").show();
                } else {
                    KR.openSelectedPaymentMethod();
                }

                this._enableButton();
                can_process_payment = false;
            },

            _processPayment: function (code, paymentOptionId, flow) {
                if (code == "lyra" && ! can_process_payment) {
                   this._lyraSubmitPayment();

                   return;
                }

                return this._super(...arguments)
            },

            _onClickPaymentOption: function (ev) {
                let providerId = $(ev.currentTarget).find('input[name="o_payment_radio"]')[0].getAttribute('data-provider');
                if (providerId != "lyra") {
                    return this._super(...arguments);
                }

                // Uncheck all radio buttons.
                this.$('input[name="o_payment_radio"]').prop('checked', false);

                // Check radio button linked to selected payment option.
                const checkedRadio = $(ev.currentTarget).find('input[name="o_payment_radio"]')[0];
                $(checkedRadio).prop('checked', true);

                // Show the inputs in case they had been hidden.
                this._showInputs();

                // Disable the submit button while building the content.
                this._disableButton(false);

                // Unfold and prepare the inline form of selected payment option.
                this._displayInlineForm(checkedRadio);
            }
        }

        Lyra_PaymentCheckoutForm.include(lyra_Mixin);
        Lyra_manageForm.include(lyra_Mixin);
    });
});