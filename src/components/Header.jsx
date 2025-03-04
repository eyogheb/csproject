import ronald from '../assets/mcd.png'

export function Header() {
    return (
        <div className="header">
            <img src={ronald} alt="Picture of Ronald McDonald" style={{ width: '10%', height: 'auto'}} />
            <h1 className="textHeading"> Ronald</h1>
        </div>
    );
}