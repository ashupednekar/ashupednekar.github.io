## Let's build our own lambda faas

### Why?

As usual, as engineers, we build things out from scratch, in order to test our own understanding of something, and discover what we don't know.

As they say,
> "We did it not cuz it's easy, but cuz we thought it was"

### So what is it?

`Serverless` functions are a way to give developers a way to build out microservices as individual functions, where all the infrastructure and setup is abstracted away in a nice interface where you can write functions in your language of choice, which would then magically become HTTP endpoints or pub/sub consumers. 

**Benefits**
- Approachable
- Can support everything u need as standard interfaces
- Pay as you go
- microservices without thinking much about it
- Easy/ automated deployment

**Downsides**
- Yet another abstraction
- You're tied to the provider's assumptions
- Hard to structure complex codebase scenarios
- Cold start problem


