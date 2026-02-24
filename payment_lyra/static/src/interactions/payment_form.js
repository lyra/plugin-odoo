/** @odoo-module */

/**
 * Copyright © Lyra Network.
 * This file is part of Lyra Collect plugin for Odoo. See COPYING.md for license details.
 *
 * @author    Lyra Network (https://www.lyra.com/)
 * @copyright Copyright © Lyra Network
 * @license   http://www.gnu.org/licenses/agpl.html GNU Affero General Public License (AGPL v3)
 */

import { patch } from '@web/core/utils/patch';
import { PaymentForm } from '@payment/interactions/payment_form';

import { lyraCheckAmount,
         lyraHidePreMessage,
         lyraPrepareInlineForm,
         lyraProcessDirectFlow,
         lyraSubmitPayment
} from '@payment_lyra/js/payment_utils';

let can_process_payment = true;

patch(PaymentForm.prototype, {
    setup() {
        super.setup();

        // Update form token on amount update.
        $(document).ready(function() {
            if (typeof (KR) == 'undefined') {
                return;
            }

            lyraCheckAmount();
            lyraHidePreMessage();
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
            await super._prepareInlineForm(...arguments);
            return;
        }

        const inlineValues = this._lyraGetInlineValues();
        if (inlineValues.length == 0) {
            return;
        }

        // Set the flow to direct to avoid redirection to payment page on Odoo payment button clic.
        this._setPaymentFlow('direct');
        this._disableButton(false);

        await lyraPrepareInlineForm(inlineValues);
    },

    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'lyra') {
            await super._processDirectFlow(...arguments);
            return;
        }

        if (! can_process_payment) {
            return;
        }

        var inlineValues = this._lyraGetInlineValues();
        await lyraProcessDirectFlow(inlineValues, processingValues);

        this._enableButton();
        can_process_payment = false;
    },

    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode == "lyra" && ! can_process_payment) {
            lyraSubmitPayment();
            this._enableButton();
            can_process_payment = false;

            return;
        }

        await super._initiatePaymentFlow(...arguments);
    }
});