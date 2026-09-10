// src/useAdobeSdk.js

import { useState, useEffect } from 'react';

const ADOBE_SDK_URL = 'https://documentservices.adobe.com/view-sdk/main.js';

let adobeSdkPromise = null;

export const useAdobeSdk = () => {
  const [isSdkReady, setIsSdkReady] = useState(false);

  useEffect(() => {
    if (window.AdobeDC) {
      setIsSdkReady(true);
      return;
    }

    if (!adobeSdkPromise) {
      adobeSdkPromise = new Promise((resolve) => {
        const script = document.createElement('script');
        script.src = ADOBE_SDK_URL;
        script.async = true;
        
        script.onload = () => {
          document.addEventListener('adobe_dc_view_sdk.ready', () => {
            resolve();
          });
        };
        
        document.body.appendChild(script);
      });
    }

    adobeSdkPromise.then(() => {
      setIsSdkReady(true);
    });

  }, []);

  return isSdkReady;
};