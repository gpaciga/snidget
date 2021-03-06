# snidget

Personal accounting tool

[![Total alerts](https://img.shields.io/lgtm/alerts/g/gpaciga/snidget.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/gpaciga/snidget/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/gpaciga/snidget.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/gpaciga/snidget/context:python)

## About Snidget

Snidget is a python program which tracks your financial information,
in particular your expenses and income. The user adds each transaction
on their accounts and snidget can provide reports about how much
you're spending.

This program was written by Gregory Paciga (`snidget@greg.paciga.com`)
in his free time. Bugs, requests, and suggestions can be sent to him,
or through GitHub.

The Snidget code is hosted at <https://github.com/gpaciga/snidget>.

The program started out being called, very creatively, "budget", then
changed to "budgie" to sound cuter, but a finance program called
"budgie" already existed, so it was renamed after another small bird
(also with a name similar to "budget") and became "snidget", which is
actually a fictional bird from the Harry Potter universe and therefore
much cooler than a budgie.


## Getting Started

Before you start using snidget, you will want to customize it a bit.
The two most important things are accounts and types.

You will want to add the accounts you are keeping track of. By default
Snidget has Bank, Credit, and Cash accounts, but you might want to
make accounts for specific banks or credit cards, for example. You
do this by running something like
```
   snidget.py -o delaccount Bank -o addaccount RBC
   snidget.py -o delaccount Credit -o addaccount Mastercard
```

You may also want to add or delete the "types". Types are categories
of transactions, for example all purchases of food could go under a
type 'Food', while all bills go under 'Bills'. Similarly to accounts,
you can add and remove types with `-o deltype` and `-o addtype`.

Use `-o help` to see what other options are available.


## Running Snidget

Most of the time you will use the `-n` and `-p` command line options
to add new transactions to your database and to print the database,
respectively. For other usage options, try `-h`.

If you run snidget without any command line arguments, a basic
graphical interface will run.



## License

See [LICENSE](LICENSE).
