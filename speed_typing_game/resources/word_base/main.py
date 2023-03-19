import random
easy_word_base = {1: 'All s well that ends well',
                  2: 'Actions speak louder than words',
                  3: 'Beauty is in the eye of the beholder',
                  4: 'Better late than never',
                  5: 'Charity begins at home',
                  6: 'Cleanliness is next to godliness',
                  7: 'Ciekawość to pierwszy stopień do piekła',
                  8: 'Co łatwo przyszło, łatwo się rozchodzi.',
                  9: 'Potrzeba jest matką wynalazku',
                  10: 'Cierpliwość to cnota.',
                  11: 'Ćwiczenie czyni mistrza',
                  12: 'Kto rano wstaje, temu Pan Bóg daje',
                  13: 'The sun is shining',
                  14: 'We are going to the park',
                  15: 'We are sitting on the couch',
                  16: 'They are swimming in the pool',
                  17: 'She is wearing a dress',
                  18: 'The flowers are blooming',
                  19: 'They are talking to each other',
                  20: 'He is listening to music',
                  21: 'Moim ulubionym kolorem jest niebieski',
                  22: 'Oni rozmawiają między sobą',
                  23: 'Oni idą na spacer do parku',
                  24: 'On jest studentem',
                  25: 'He is riding a bike'}

medium_word_base = {
    1: 'To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.',
    2: 'Success is not final, failure is not fatal: It is the courage to continue that counts.',
    3: 'Believe you can and you are halfway there.',
    4: 'The best way to predict the future is to create it.',
    5: 'You miss 100% of the shots you don’t take.',
    6: 'If you want to go fast, go alone. If you want to go far, go together.',
    7: 'The only way to do great work is to love what you do.',
    8: 'You can never cross the ocean until you have the courage to lose sight of the shore.',
    9: 'If you don’t stand for something, you will fall for anything.',
    10: 'In the end, we only regret the chances we didn’t take.',
    11: 'It does not matter how slowly you go as long as you do not stop.',
    12: 'The only thing necessary for the triumph of evil is for good men to do nothing.',
    13: 'Happiness is not something ready made. It comes from your own actions.',
    14: 'The journey of a thousand miles begins with one step.',
    15: 'A person who never made a mistake never tried anything new.',
    16: 'I have not failed. I have just found 10,000 ways that won’t work.',
    17: 'People often say that motivation doesn’t last. Well, neither does bathing – that’s why we recommend it daily.',
    18: 'If you want to live a happy life, tie it to a goal, not to people or things.',
    19: 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
    20: 'Our greatest weakness lies in giving up. The most certain way to succeed is always to try just one more time.',
    21: 'If you look at what you have in life, you’ll always have more. If you look at what you don’t have in life, you’ll never have enough.',
    22: 'Life is 10% what happens to you and 90% how you react to it.',
    23: 'I can’t change the direction of the wind, but I can adjust my sails to always reach my destination.',
    24: 'You are never too old to set another goal or to dream a new dream.',
    25: 'It’s not the years in your life that count. It’s the life in your years.'}

difficult_word_base = {1: 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
                       2: 'In three words I can sum up everything I’ve learned about life: it goes on.',
                       3: 'Education is the most powerful weapon which you can use to change the world.',
                       4: 'The future belongs to those who believe in the beauty of their dreams.',
                       5: 'Darkness cannot drive out darkness; only light can do that. Hate cannot drive out hate; only love can do that.',
                       6: 'If you want to change the world, pick up a pen and write.',
                       7: 'It always seems impossible until it’s done.',
                       8: 'The greatest glory in living lies not in never falling, but in rising every time we fall.',
                       9: 'I have learned over the years that when one’s mind is made up, this diminishes fear.',
                       10: 'The power of imagination makes us infinite.',
                       11: 'In the end, we will remember not the words of our enemies, but the silence of our friends.',
                       12: 'The only true wisdom is in knowing you know nothing.',
                       13: 'I am not a product of my circumstances. I am a product of my decisions.',
                       14: 'If you want to make peace with your enemy, you have to work with your enemy. Then he becomes your partner.',
                       15: 'I have a dream that one day this nation will rise up and live out the true meaning of its creed: “We hold these truths to be self-evident, that all men are created equal.”',
                       16: 'We can’t help everyone, but everyone can help someone.',
                       17: 'It is during our darkest moments that we must focus to see the light.',
                       18: 'I’ve missed more than 9000 shots in my career. I’ve lost almost 300 games. 26 times I’ve been trusted to take the game-winning shot and missed. I’ve failed over and over and over again in my life. And that is why I succeed.',
                       19: 'If you’re going through hell, keep going.',
                       20: 'The best revenge is massive success.',
                       21: 'A person who never made a mistake never tried anything new.',
                       22: 'The only way to do great work is to love what you do. If you haven’t found it yet, keep looking. Don’t settle. As with all matters of the heart, you’ll know when you find it.',
                       23: 'Success is not the key to happiness. Happiness is the key to success. If you love what you are doing, you will be successful.',
                       24: 'The greatest wealth is to live content with little.',
                       25: 'No one can make you feel inferior without your consent.'}

def word_base(level):
    n = random.randint(1, 25) ## n-random number(1,25)
    sentence = " "
    if (level == 'k'): ## k-easy
        sentence += easy_word_base[n]
        return sentence
    if (level == 'l'): ## l-medium
        sentence += medium_word_base[n]
        return sentence
    if (level == 'm'): ## m-hard
        sentence += difficult_word_base[n]
        return sentence
def main():
    print("Choose difficulty level:\n"
          "k - easy\n"
          "l - medium\n"
          "m - hard\n")
    level = (input("Press:\n"))
    print(word_base(level))
main()
