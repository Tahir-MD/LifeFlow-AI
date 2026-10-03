import React from "react";
import { DropletIcon, HeartIcon } from "./Icons.jsx";

/**
 * A consistent two-panel template for every sign-up and login page:
 * a colored, icon-led panel on one side describing who the page is
 * for, and the actual form on the other. Every auth page in the app
 * uses this, so they all share one professional look instead of each
 * being a bare form on a blank page.
 */
export default function AuthLayout({ icon: Icon = DropletIcon, eyebrow, title, tagline, children }) {
  return (
    <div className="auth-split">
      <div className="auth-side">
        <div className="auth-side-shape" aria-hidden="true">
          <HeartIcon size={220} color="#FFFFFF" filled />
        </div>
        <div className="auth-side-content">
          <div className="auth-side-icon"><Icon size={30} color="#FFFFFF" /></div>
          <span className="auth-side-eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
          <p>{tagline}</p>
        </div>
      </div>
      <div className="auth-form-panel">
        <div className="auth-form-inner">{children}</div>
      </div>
    </div>
  );
}
