# PayZen Odoo

PayZen Odoo is an open source payment module that links Odoo based e-commerce websites to PayZen secured payment gateway developped by Lyra Network https://www.lyra-network.com/.

For more information about PayZen, see https://payzen.eu/.

# Installation & Upgrade

- Delete payment_payzen folder from [ODOO_ROOT_FOLDER]/server/odoo/addons directory if already installed.
- Download module archive from releases tab or in https://payzen.io/fr-FR/module-de-paiement-gratuit/#odoo.
- Unzip archive to odoo_x.y.z folder.
- Copy payment_payzen directory to [ODOO_ROOT_FOLDER]/server/odoo/addons directory.
- Retsart Odoo server with *sudo service odoo restart* on Linux systems or by restarting Windows Odoo service.
- In your Odoo administrator interface, browse to "Applications" tab.
- Delete "Applications" filter from search field and search for "payzen" keyword.
- Click "Install" (or "Upgrade") button of the "PayZen Payment Acquirer" module.

# Configuration

- Go to "Website Admin" tab.
- In "Configuration" section, expand "eCommerce" menu than click on "Payment Acquirers" entry.
- Click on button "Configure" of PayZen module.
- You can now enter PayZen credentials.
