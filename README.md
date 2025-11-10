# Ray

Ray is an open-source unified framework designed to scale Python application from a laptop to a large cluster with minimal code changes. 

It’s built on two main layers:

- Ray Core
>   - Tasks: Stateless functions executed in the cluster.
>   - Actors: Stateful worker processes created in the cluster.
>   - Objects: Immutable values accessible across the cluster.

- Ray AI Libraries
>   - Ray Data: Scalable data processing.
>   - Ray Train: Distributed training.
>   - Ray Tune: Hyperparameter tuning.
>   - Ray Serve: Model serving.
>   - RLlib: Scalable reinforcement learning

---

# Why Ray?

Modern AI and ML models are growing more complex and data-intensive; even with specialized hardware, single-machine computing is no longer sufficient for large-scale training and data processing. And the only way to manage this workload is through distributed and parallel computing.

Here comes Ray, a unified way to scale Python and AI applications from a laptop to a cluster.

With Ray, you can seamlessly scale the same code from a laptop to a cluster. Ray is a general-purpose framework, meaning that it can handle any type of workload.

---

To start with install Ray with: pip install ray, see the [Installation page](https://docs.ray.io/en/latest/ray-overview/installation.html) for more info.

---

# Sources

[Documentation](https://docs.ray.io/en/latest/index.html)
