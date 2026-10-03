import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { getPlatformStats } from "../services/api";
import {
  DropletIcon, HospitalIcon, ShieldCheckIcon, MapPinIcon, PhoneIcon, MailIcon,
  ClockIcon, UsersIcon, StarIcon, BoxIcon, BellRingIcon, HeartPulseIcon,
  CheckCircleIcon, ArrowRightIcon, HeartIcon,
} from "../components/Icons.jsx";

const FEATURES = [
  {
    icon: BoxIcon,
    title: "Hospital stock checked first",
    text: "Every request is matched against real hospital blood-bank inventory before any donor is ever contacted, so existing stock is used first and donors are only asked for the genuine shortfall.",
  },
  {
    icon: HeartPulseIcon,
    title: "Smart, life-saving matching",
    text: "Blood-type compatibility, distance, and donor eligibility are checked instantly, ranking the closest safe donors for every request.",
  },
  {
    icon: ShieldCheckIcon,
    title: "Full detail before you decide",
    text: "Donors see the complete picture — patient, hospital, urgency, and units needed — before choosing to accept or decline a request.",
  },
  {
    icon: StarIcon,
    title: "Ratings you can trust",
    text: "Donors, hospitals, and patients rate each other after every donation, so reputations are earned and visible platform-wide.",
  },
  {
    icon: BellRingIcon,
    title: "Real-time notifications",
    text: "Instant alerts the moment a compatible request opens nearby, a donor accepts, or a hospital publishes a donation camp.",
  },
  {
    icon: UsersIcon,
    title: "Every history, saved",
    text: "Donors, hospitals, and patients each keep a permanent, private history tied to their account — log back in any time to see it.",
  },
];

const DONOR_STEPS = [
  { title: "Create your donor profile", text: "Register with your blood type and location in under a minute." },
  { title: "Get matched automatically", text: "We notify you the instant a compatible request opens nearby." },
  { title: "Review the full request", text: "See the patient, hospital, urgency, and units needed before you decide." },
  { title: "Accept, donate, get rated", text: "Confirm how many bags you're giving, donate, and earn points and a rating." },
];

const SEEKER_STEPS = [
  { title: "Register as a hospital or patient", text: "Hospitals verify with a license number; patients register with a CNIC." },
  { title: "We check hospital stock first", text: "Your request is matched against nearby blood-bank inventory automatically." },
  { title: "Only the shortfall goes to donors", text: "If stock isn't enough, compatible nearby donors are notified instantly." },
  { title: "Track it end-to-end", text: "See who's coming, rate the donor, and keep the record in your history forever." },
];

function StatBlock({ value, label }) {
  return (
    <div className="stat">
      <div className="figure">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}

const ABOUT_POINTS = [
  "Built specifically for how blood actually moves: from a hospital's own fridge first, then to the nearest willing donor only if there's a real shortfall.",
  "One shared, permanent history for every donor, patient, and hospital — nothing is ever lost between logins.",
  "Works the same whether a request comes from a hospital's front desk or straight from a worried family member.",
];

export default function Home() {
  const [platformStats, setPlatformStats] = useState(null);
  const location = useLocation();

  useEffect(() => {
    getPlatformStats()
      .then((response) => setPlatformStats(response.data))
      .catch(() => setPlatformStats(null));
  }, []);

  useEffect(() => {
    if (!location.hash) return;
    const target = document.querySelector(location.hash);
    if (target) {
      // A tiny delay lets the page finish laying out first, so the
      // scroll lands on the right spot instead of an old position.
      setTimeout(() => target.scrollIntoView({ behavior: "smooth", block: "start" }), 60);
    }
  }, [location]);

  return (
    <div>
      {/* ---------------- Hero ---------------- */}
      <section className="hero-split">
        <div className="page hero-split-inner">
          <div className="hero-copy">
            <span className="eyebrow"><DropletIcon size={15} /> Blood bank &amp; donor network</span>
            <h1>Every two seconds, someone needs blood.</h1>
            <p className="lede">
              LifeFlow is a blood bank and donor network that connects patients, hospitals, and
              volunteer donors in real time. Requests are matched by blood type and distance,
              hospitals manage their own stock and staff shifts, and every donation is recorded
              so nothing is ever lost.
            </p>
            <div className="stat-row">
              <StatBlock value={platformStats ? platformStats.total_donors : "—"} label="registered donors" />
              <StatBlock value={platformStats ? platformStats.total_hospitals : "—"} label="partner hospitals" />
              <StatBlock value={platformStats ? platformStats.total_units_donated : "—"} label="bags donated" />
              <StatBlock
                value={platformStats && platformStats.average_platform_rating ? `${platformStats.average_platform_rating}★` : "New"}
                label="average platform rating"
              />
            </div>
          </div>
          <div className="hero-media">
            <img
              className="hero-photo"
              src="https://images.unsplash.com/photo-1615461066159-fea0960485d5?auto=format&fit=crop&w=900&q=80"
              alt="A donor giving blood at a modern blood donation drive"
              loading="eager"
            />
            <div className="hero-photo-badge">
              <ShieldCheckIcon size={20} color="#0E3B36" />
              <div>
                <strong>Stock-checked</strong>
                <span>before every donor call-out</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- About ---------------- */}
      <section className="page section" id="about">
        <div className="about-grid">
          <div className="about-media">
            <img
              src="https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&w=800&q=80"
              alt="A hospital blood bank technician checking donation bags"
            />
            <div className="about-shape" aria-hidden="true">
              <HeartIcon size={130} color="#B01E28" filled />
            </div>
          </div>
          <div className="about-copy">
            <span className="eyebrow">About LifeFlow</span>
            <h2>A blood bank network, not just a donor list</h2>
            <p className="section-lede">
              LifeFlow was built around one simple idea: the fastest, safest unit of blood
              is usually already sitting in a hospital fridge. So instead of treating every
              request as a call for a new donor, LifeFlow checks real hospital inventory
              first, and only reaches out to the nearest compatible donor for whatever is
              genuinely still needed — whether that request comes from a hospital's front
              desk or directly from a patient's family.
            </p>
            <ul className="about-points">
              {ABOUT_POINTS.map((point) => (
                <li key={point}>
                  <CheckCircleIcon size={18} color="#0E3B36" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* ---------------- Features ---------------- */}
      <section className="page section">
        <div className="section-head">
          <span className="eyebrow">Why LifeFlow</span>
          <h2>Built for the moment blood is needed most</h2>
          <p className="section-lede">A modern blood bank platform that connects donors, patients, and hospitals with one shared, transparent history.</p>
        </div>
        <div className="feature-grid">
          {FEATURES.map((feature) => (
            <div className="feature-card" key={feature.title}>
              <div className="feature-icon"><feature.icon size={24} color="#B01E28" /></div>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section className="section section-alt">
        <div className="page">
          <div className="section-head">
            <span className="eyebrow">Guidance</span>
            <h2>How the app works</h2>
            <p className="section-lede">Two short journeys — whichever side of a donation you're on.</p>
          </div>
          <div className="steps-columns">
            <div className="steps-col">
              <h3 className="steps-col-title"><DropletIcon size={20} color="#B01E28" /> For donors</h3>
              <ol className="steps-list">
                {DONOR_STEPS.map((step, index) => (
                  <li key={step.title}>
                    <span className="step-num">{index + 1}</span>
                    <div>
                      <strong>{step.title}</strong>
                      <p>{step.text}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
            <div className="steps-col">
              <h3 className="steps-col-title"><HospitalIcon size={20} color="#0E3B36" /> For hospitals &amp; patients</h3>
              <ol className="steps-list">
                {SEEKER_STEPS.map((step, index) => (
                  <li key={step.title}>
                    <span className="step-num step-num-alt">{index + 1}</span>
                    <div>
                      <strong>{step.title}</strong>
                      <p>{step.text}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- Gallery / trust ---------------- */}
      <section className="page section">
        <div className="section-head">
          <span className="eyebrow">Inside LifeFlow</span>
          <h2>A network you can see and trust</h2>
        </div>
        <div className="gallery-grid">
          <img src="https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=700&q=80" alt="Hospital blood bank refrigerator with labeled blood bags" />
          <img src="https://images.unsplash.com/photo-1587854692152-cbe660dbde88?auto=format&fit=crop&w=700&q=80" alt="Medical staff preparing a donation" />
          <img src="https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?auto=format&fit=crop&w=700&q=80" alt="Volunteer donor smiling after giving blood" />
        </div>
      </section>

      {/* ---------------- Ratings / testimonial ---------------- */}
      <section className="section section-alt">
        <div className="page rating-band">
          <div className="rating-band-score">
            <div className="rating-band-number">
              {platformStats && platformStats.average_platform_rating ? platformStats.average_platform_rating : "—"}
            </div>
            <div className="rating-band-stars">
              {[1, 2, 3, 4, 5].map((n) => (
                <StarIcon key={n} size={18} color="#B01E28" filled={platformStats && platformStats.average_platform_rating >= n - 0.5} />
              ))}
            </div>
            <p>Average rating across every completed donation, given by donors, hospitals, and patients about each other.</p>
          </div>
          <blockquote className="rating-quote">
            “The stock check meant our patient's family didn't need a single donor call — the
            hospital already had what was needed on the shelf, and LifeFlow found it in seconds.”
            <footer>— A partner hospital coordinator</footer>
          </blockquote>
        </div>
      </section>

      {/* ---------------- Contact & location ---------------- */}
      <section className="page section" id="contact">
        <div className="section-head">
          <span className="eyebrow">Contact &amp; location</span>
          <h2>Talk to the LifeFlow team</h2>
        </div>
        <div className="contact-grid">
          <div className="contact-card">
            <MapPinIcon size={22} color="#B01E28" />
            <h3>Head office</h3>
            <p>LifeFlow Blood Network<br />2nd Floor, Clifton Business Tower<br />Karachi, Sindh, Pakistan</p>
          </div>
          <div className="contact-card">
            <PhoneIcon size={22} color="#B01E28" />
            <h3>24/7 emergency line</h3>
            <p>+92 300 1234567<br />Available around the clock for urgent requests.</p>
          </div>
          <div className="contact-card">
            <MailIcon size={22} color="#B01E28" />
            <h3>Email support</h3>
            <p>support@lifeflow.app<br />Replies within one business day.</p>
          </div>
          <div className="contact-card">
            <ClockIcon size={22} color="#B01E28" />
            <h3>Support hours</h3>
            <p>Live chat: 8am – 10pm daily<br />Emergency matching: always on.</p>
          </div>
        </div>
      </section>

      {/* ---------------- Final CTA ---------------- */}
      <section className="section cta-band">
        <div className="page cta-band-inner">
          <div>
            <h2>Ready to save a life today?</h2>
            <p>Registration takes under two minutes, for donors, patients, and hospitals alike.</p>
          </div>
          <div className="hero-actions">
            <Link to="/donor/register" className="btn">Become a donor <ArrowRightIcon size={16} /></Link>
            <Link to="/receiver/register" className="btn btn-outline">I need blood</Link>
            <Link to="/hospital/register" className="btn btn-outline">Register hospital</Link>
          </div>
        </div>
      </section>

      {/* ---------------- Footer ---------------- */}
      <footer className="site-footer">
        <div className="page footer-inner">
          <div className="footer-brand">
            <span className="nav-logo"><DropletIcon size={20} color="#B01E28" /> LifeFlow</span>
            <p>A modern blood bank and donor network connecting patients, hospitals, and donors in real time.</p>
          </div>
          <div className="footer-links">
            <div>
              <h4>Get involved</h4>
              <Link to="/donor/register">Become a donor</Link>
              <Link to="/receiver/register">Request blood</Link>
              <Link to="/hospital/register">Register a hospital</Link>
            </div>
            <div>
              <h4>Explore</h4>
              <Link to="/leaderboard">Donor leaderboard</Link>
              <a href="#about">About LifeFlow</a>
              <a href="#contact">Contact &amp; location</a>
            </div>
            <div>
              <h4>Contact</h4>
              <span><CheckCircleIcon size={14} color="#0E3B36" /> support@lifeflow.app</span>
              <span><CheckCircleIcon size={14} color="#0E3B36" /> +92 300 1234567</span>
            </div>
          </div>
        </div>
        <div className="footer-bottom">© {new Date().getFullYear()} LifeFlow Blood Network. All rights reserved.</div>
      </footer>
    </div>
  );
}
