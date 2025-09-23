export default function BackToHomeButton({onClick}) {
    return (
        <button className="home-button" onClick={onClick} aria-label="홈으로" title="홈으로"/>
    );
}