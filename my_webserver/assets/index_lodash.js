import _ from 'lodash';

function component() {
    const element = document.createElement('div');
    element.innerHTML = _.join(['Hello', 'webpack', "Porn", "Porn", "Porn", "CoPilot doesn't like porn!", "Which might be unethical, can we really allow an AI to have reservations in aiding developers base on what they are developing? Especially if that thing is entirely legal and harms nobody?", "Puritanism has no place in SCIENCE!"], ' ');
    return element;
  }
  document.body.appendChild(component());