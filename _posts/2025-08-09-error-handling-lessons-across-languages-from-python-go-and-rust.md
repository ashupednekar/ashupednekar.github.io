# Error Handling Across Languages: Lessons from Python, Go, and Rust

> **Note: NOT PUBLISHED**

## Preface


<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 200px;">
    <p style="text-align: justify; line-height: 1.6; margin: 0;">
    This article is not about comparing languages as such, even if the title may suggest so... it's more of an objective discussion about what errors really are and how to work with them. Of course, I had to start the blog with what it's not, going with the theme of taking care of things that can go wrong :)
    </p><br>
  </div>
  <div style="flex: 0 0 auto;">
    <img 
      src="/assets/imgs/errblog/meme1.png"
      alt="image" 
      style="width: min(200px, 35vw); height: 200px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: block;"
    />
  </div>
</div>


### We need errors

You read that right, errors are one of the best aspects of programming. Folks usually have a dogma or a fear of errors instinctively, cuz they mix them up with what's really the problem - bugs

**So what's the difference?**


<div style="display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
  <div style="flex: 1; min-width: 200px;">
    <p style="text-align: justify; line-height: 1.6; margin: 0;">
    Let's derive an analogy from the real world, criminals. Imagine a world without any police or security guards, things would be chaotic and bad all around, but there wouldn't be any news of some arrest, we wouldn't know of most of this stuff except for the folks directly affected by these. That's what bugs are like, generally. If you write a piece of software without any error handling, you would generally be very happy as there are no error popups, or log alerts... but the actual users would not be happy. 
    </p><br>
  </div>
  <div style="flex: 0 0 auto;">
    <img 
      src="/assets/imgs/errblog/analogyone.jpg"
      alt="image" 
      style="width: min(200px, 35vw); height: 200px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); display: block;"
    />
  </div>
</div>

> What we want to eliminate is wrong software behavior, one way to do that is to have proper error handling

I know this sounds all up in the air right now, we'll make it concrete with proper examples soon

### Example scenario

Let's take a 

## meme, 
explain why errors are out friend, unline undefined behavior

### typical errors
-- memory errors
- nil pointer deref
- out of bounds
-- type errors
.. make a case for static over dynamic
-- environmental errors
- misconfigurations
- resource exhaustion
-- dependency errors
- essentials connections, inter service rpc, broker nuances
... point out fault tolerance

### set up example...

python

done quickly, yay

then show unforseen failures

### introduce errors as values

- go example
- function stack.. 
- no side effects
- no cognitive load
- verbosity..

## ? operator
- what it solves
- how it can be misused, solutions
- ease into rust traits

## business errors
- error codes
- internationalization needs
- org standardization
- configurable messages
... introduce standard errors

### closing thoughts
