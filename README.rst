.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL v3

===================================================
Lyra Collect best plugin for Odoo
===================================================

Lyra Collect plugin for Odoo is an open source plugin that links Odoo based e-commerce websites to Lyra Collect
secure payment gateway developed by `Lyra Network <https://www.lyra.com/>`_.

Installation & Upgrade
======================

Download the module archive from gateway resources website (menu E-commerce > Free payment plugins).

If already installed, you must delete the old payment_lyra folder. You will find already installed
addons in either:

* [ODOO_ROOT_FOLDER]/server/odoo/addons/
* /var/lib/odoo/addons/[VERSION]/ (on Linux only)
* `addons_path` defined in odoo.conf

Now unzip the downloaded archive and copy the new payment_lyra folder to Odoo addons directory. Then, you
can choose one of these instructions:

* In your Odoo administrator interface, browse to "Configuration" tab. Here in, activate the developer mode.
  Then browse to "Applications" tab and click on "Update applications list".
* Or restart Odoo server with *sudo systemctl restart odoo* on Linux or by restarting Windows Odoo service.
  Odoo will update the applications list on startup.

In your Odoo administrator interface, browse to "Applications" tab, delete "Applications" filter from
search field and search for "lyra" keyword. Click "Install" (or "Upgrade") button of the "Lyra Collect
Payment Acquirer" module.

Configuration
=============

* Go to "Website Admin" tab.
* In "Configuration" section, expand "eCommerce" menu than click on "Payment Acquirers" entry.
* Click on button "Configure" of Lyra Collect module.
* You can now enter your Lyra Collect credentials.

IMPORTANT
---------
* You should select a Payment Journal in the "Configuration" tab of the Lyra Collect aquirer
  to start using this payment method.
* If you have multiple Odoo databases on your server, do not forget to set dbfilter
  parameter in odoo.conf. *You must launch one database only per URL* because Lyra Collect
  have to send back payment notification on the right database. Otherwise it will
  fail with a 404 error.

Author
=======

* Lyra Network (https://www.lyra.com/)

License
=======

Each Lyra Collect plugin source file included in this distribution is licensed under
the Affero General Public License (AGPL 3.0).

Please see LICENSE.txt for the full text of the AGPL 3.0 license.
It is also available through the world-wide-web at this URL: http://www.gnu.org/licenses/agpl.html.