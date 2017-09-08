# D2D Scheduler

The D2D scheduler is a uniflex control application that can be used to schedule content exchanges between content providers and consumers. 

It requires uniflex, a framework for simplifying wireless network control.

https://github.com/uniflex/manifests

# Usage
After installing and enabling uniflex the scheduler is started by calling:

```sh
uniflex-agent --config ./config.yaml
```

It is required to update the ZeroMQ information in the config.yaml

# Contact

Niels Karowski (karowski@tkn.tu-berlin.de)
