This page summarises the different levels at which one might want/need to implement tests for the [SONATA](http://www.sonata-nfv.eu)'s Service Platform Gatekeeper.

# Generic architecture
The generic architecture of our micro-services is shown below.

![](https://www.planttext.com/plantuml/img/ZP8noy8m48Rt_8h3lKCoIz59nENRFnn2VB71jYdNgulutqqJhOeApN1SZYSynqjMlLYMeQcLUAb16xHWxwZnZaFHWy_UeIVBhl829mD3gSwwaps25XihE04TU46Nb_6Erd_RSKJnkD1qeKKhzBzSSXW4PRadsrFgFv4c753VaTIhgw8NwTjgfETfz0oFZg9V6ZDFOsPeJDHSdvuW5PWUIN_HJEr-t2y6IqLvpoxLyPfpIfKAziTA7epEa9ue_HKp6JCJPZAMtaqRv9bvdwaLsaFyGJS0)

In this picture we can see that every micro-service component is accessed trhough a ***route*** kind of component, which then delegates to a ***model*** kind of component. A ***route*** kind of component accepts only a set of pre-defined routes, validates headers and the parameters it is meaningfull to be valitade at this stage (*e.g.*, UUID format). A ***model*** kind of component does all the remaining work, either by it self or by cooperating with the other components. **Model** can talk to other models within the same micro-service. When services form another micro-service are needed, **models** talk to a **route** of the needed service.

This *micro-architecture* is repeated throughout all micro-services of the **Gatekeeper**. External services are accessed through a ***model*** component.

# Possible test levels
From the previously described architecture, we can envisage the following test levels:

* **Unit tests:** for each one of the ***route*** and ***model*** components;
* **Micro-service tests:** for each one of the ***micro-services*** (in the above picture, this would mean the ***GK API***, the ***micro-service 1*** and the ***micro-service 2*** micro-services);
* **Module tests:** this level of tests would test the **Gatekeeper** as a whole;
* **Integration Tests:** this level of tests would test the integration between the **Gatekeeper** and the other **services** (e.g., the **Catalogues**, the **MANO Framework**, etc.).

If we try to implement tests for every feature at every level, we'll quickly be overwhelemed by its number and the effort to maintain them.