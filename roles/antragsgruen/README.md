Role Name
=========

This role roles out Antragsgrün

Requirements
------------

None.

Role Variables
--------------


Dependencies
------------
- init_from_inventory
- hs_cleanup_subdoms

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:
```yaml
- hosts: servers
  roles:
  - role: antragsgruen
    mail_from_name: 'Antragsgrün'
    mail_from_address: "antrag@{{ hostvars[inventory_hostname].domain }}"
    dbname: "{{ hostvars[inventory_hostname].mysql.table }}"
    dbuser: "{{ hostvars[inventory_hostname].mysql.user }}"
    dbpass: "{{ hostvars[inventory_hostname].mysql.pass }}"
    domain: "{{ hostvars[inventory_hostname].domain }}"
    seed: "{{ lookup('community.general.random_string', base64=True, length=20, seed={{ inventory_hostname }}) }}"
```
License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
